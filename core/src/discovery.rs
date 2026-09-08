use anyhow::{bail, Context, Result};
use base64::{engine::general_purpose::STANDARD, Engine};
use ed25519_dalek::{Signature, VerifyingKey};
use serde::{Deserialize, Serialize};
use std::{collections::HashSet, net::SocketAddr, path::PathBuf, sync::Arc, time::{Duration, SystemTime, UNIX_EPOCH}};
use tokio::sync::RwLock;
const DOMAIN: &[u8] = b"family-connect/network-state/v1\0";
const MAX_STATE: usize = 65536;

#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Envelope { pub payload: String, pub signature: String }
#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Node {
    pub identity: String, pub name: String, pub endpoint: SocketAddr,
    pub role: String, pub internet_exit: bool, pub cert_sha256: String,
    pub server_name: String,
}
#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Device { pub identity: String, pub cert_sha256: String }
#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct State {
    pub version: u64, pub epoch: u64, pub issued_at: u64, pub expires_at: u64,
    pub nodes: Vec<Node>, pub devices: Vec<Device>,
}
pub fn now() -> u64 { SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs() }
fn fingerprint(value: &str) -> bool { value.len() == 64 && value.bytes().all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase()) }
impl State {
    pub fn valid(&self) -> bool { self.issued_at <= now() && now() < self.expires_at }
    pub fn device_allowed(&self, pin: &str) -> bool { self.valid() && self.devices.iter().any(|d| d.cert_sha256 == pin) }
    pub fn node(&self, name: &str, role: &str) -> Result<Node> {
        if !self.valid() { bail!("network lease expired"); }
        self.nodes.iter().find(|n| n.name == name && n.role == role).cloned().context("authorized node missing")
    }
}
pub fn verify(bytes: &[u8], root: &[u8], at: u64) -> Result<(Envelope, State)> {
    if bytes.len() > MAX_STATE { bail!("oversized envelope"); }
    let envelope: Envelope = serde_json::from_slice(bytes)?;
    let raw = STANDARD.decode(&envelope.payload)?;
    let key = VerifyingKey::from_bytes(root.try_into().context("invalid root size")?)?;
    key.verify_strict(&[DOMAIN, &raw].concat(), &Signature::from_slice(&STANDARD.decode(&envelope.signature)?)?)?;
    let state: State = serde_json::from_slice(&raw)?;
    if state.version != 2 || state.epoch == 0 || state.issued_at > at || state.expires_at <= at
        || state.expires_at <= state.issued_at || state.expires_at - state.issued_at > 3600 {
        bail!("invalid state version or validity");
    }
    if state.nodes.len() > 128 || state.devices.len() > 128 { bail!("catalog capacity exceeded"); }
    let mut ids = HashSet::new();
    let mut names = HashSet::new();
    let mut pins = HashSet::new();
    for node in &state.nodes {
        if !fingerprint(&node.identity) || !fingerprint(&node.cert_sha256)
            || !ids.insert(&node.identity) || !names.insert(&node.name) || !pins.insert(&node.cert_sha256)
            || !matches!(node.role.as_str(), "relay" | "gateway")
            || (node.role == "relay" && node.internet_exit)
            || node.name.is_empty() || node.endpoint.port() == 0 || node.endpoint.ip().is_unspecified()
            || node.endpoint.ip().is_multicast() || node.server_name.is_empty() {
            bail!("invalid node or relay exit");
        }
    }
    for device in &state.devices {
        if !fingerprint(&device.identity) || !fingerprint(&device.cert_sha256)
            || !ids.insert(&device.identity) || !pins.insert(&device.cert_sha256) {
            bail!("invalid device");
        }
    }
    Ok((envelope, state))
}
fn nonrollback(old: &State, new: &State) -> Result<()> {
    if (new.epoch, new.issued_at) < (old.epoch, old.issued_at) { bail!("catalog rollback"); }
    if new.epoch == old.epoch && (serde_json::to_vec(&new.nodes)? != serde_json::to_vec(&old.nodes)?
        || serde_json::to_vec(&new.devices)? != serde_json::to_vec(&old.devices)?) { bail!("membership changed without epoch increment"); }
    Ok(())
}

pub struct Discovery {
    pub state: Arc<RwLock<State>>,
    root: Vec<u8>, cache: PathBuf, urls: Vec<String>, client: reqwest::Client,
}
impl Discovery {
    async fn fetch(&self) -> Result<Vec<u8>> {
        for url in &self.urls {
            let result: Result<Vec<u8>> = async {
                let mut response = self.client.get(url).send().await?.error_for_status()?;
                let mut data = Vec::new();
                while let Some(chunk) = response.chunk().await? {
                    if data.len() + chunk.len() > MAX_STATE { bail!("oversized catalog"); }
                    data.extend_from_slice(&chunk);
                }
                Ok(data)
            }.await;
            if let Ok(bytes) = result {
                if let Ok((_, candidate)) = verify(&bytes, &self.root, now()) {
                    if nonrollback(&*self.state.read().await, &candidate).is_ok() { return Ok(bytes); }
                }
            }
        }
        bail!("no trusted bootstrap response")
    }
    pub async fn start() -> Result<Arc<Self>> {
        let root = std::fs::read(std::env::var("TRUST_ROOT_FILE")?)?;
        let cache = PathBuf::from(std::env::var("CATALOG_CACHE")?);
        let urls = std::env::var("BOOTSTRAP_URLS")?.split(',').map(str::to_string).collect();
        // Expired cache still authenticates the rollback high-water mark. It does
        // not authorize connections. The signature is checked at its issue time.
        let previous = if cache.exists() {
            let bytes = std::fs::read(&cache)?;
            let env: Envelope = serde_json::from_slice(&bytes)?;
            let payload: State = serde_json::from_slice(&STANDARD.decode(env.payload)?)?;
            Some(verify(&bytes, &root, payload.issued_at)?.1)
        } else { None };
        let floor = previous.clone().unwrap_or(State { version: 2, epoch: 0, issued_at: 0, expires_at: 0, nodes: vec![], devices: vec![] });
        let this = Arc::new(Self { state: Arc::new(RwLock::new(floor)), root, cache, urls,
            client: reqwest::Client::builder().timeout(Duration::from_secs(3))
                .redirect(reqwest::redirect::Policy::none()).build()? });
        if let Ok(bytes) = this.fetch().await { this.accept(&bytes).await?; }
        else if !this.state.read().await.valid() { bail!("no valid signed state or cache"); }
        let worker = this.clone();
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_secs(5)).await;
                if let Ok(bytes) = worker.fetch().await {
                    if worker.accept(&bytes).await.is_err() { eprintln!("catalog update rejected"); }
                }
            }
        });
        Ok(this)
    }
    async fn accept(&self, bytes: &[u8]) -> Result<()> {
        let (_, new) = verify(bytes, &self.root, now())?;
        let mut old = self.state.write().await;
        nonrollback(&old, &new)?;
        let parent = self.cache.parent().context("cache parent missing")?;
        std::fs::create_dir_all(parent)?;
        // Cache and high-water mark are one signed atomic file, not two files
        // that can diverge on a crash. Fsync before publishing the new state.
        let temp = self.cache.with_extension("tmp");
        use std::io::Write;
        let mut file = std::fs::File::create(&temp)?;
        file.write_all(bytes)?; file.sync_all()?;
        std::fs::rename(temp, &self.cache)?;
        std::fs::File::open(parent)?.sync_all()?;
        *old = new;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ed25519_dalek::{Signer, SigningKey};
    fn signed(state: &State) -> (Vec<u8>, Vec<u8>) {
        let key = SigningKey::from_bytes(&[7u8;32]);
        let bytes = serde_json::to_vec(state).unwrap();
        let envelope = Envelope { payload: STANDARD.encode(&bytes), signature: STANDARD.encode(key.sign(&[DOMAIN,&bytes].concat()).to_bytes()) };
        (serde_json::to_vec(&envelope).unwrap(), key.verifying_key().to_bytes().to_vec())
    }
    fn state() -> State { State { version:2,epoch:1,issued_at:100,expires_at:200,nodes:vec![],devices:vec![] } }
    #[test] fn signatures_time_and_rollback() {
        let s=state(); let (bytes,key)=signed(&s);
        assert!(verify(&bytes,&key,150).is_ok());
        assert!(verify(&bytes,&key,99).is_err()); assert!(verify(&bytes,&key,200).is_err());
        assert!(verify(&bytes,&[8u8;32],150).is_err());
        let mut changed=s.clone(); changed.epoch=2;
        assert!(nonrollback(&changed,&s).is_err());
        changed=s.clone(); changed.issued_at=101;
        assert!(nonrollback(&changed,&s).is_err());
        let mut invalid=bytes.clone(); invalid[20]^=1;
        assert!(verify(&invalid,&key,150).is_err());
    }
    #[test] fn relay_cannot_be_exit_or_reuse_device_identity() {
        let mut s=state();
        s.nodes.push(Node { identity:"a".repeat(64),name:"relay".into(),endpoint:"127.0.0.1:4433".parse().unwrap(),
            role:"relay".into(),internet_exit:true,cert_sha256:"b".repeat(64),server_name:"relay.test".into() });
        let (bytes,key)=signed(&s); assert!(verify(&bytes,&key,150).is_err());
        s.nodes[0].internet_exit=false;
        let (bytes,key)=signed(&s); assert!(verify(&bytes,&key,150).is_ok());
        s.devices.push(Device {identity:"a".repeat(64),cert_sha256:"c".repeat(64)});
        let (bytes,key)=signed(&s); assert!(verify(&bytes,&key,150).is_err());
    }
}
