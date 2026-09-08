//! Phase 0 laboratory: inner QUIC survives replacement of a UDP relay path.
//! Relay destination is operator configuration, NEVER an input packet field.
use anyhow::{bail, Context, Result};
use quinn::{ClientConfig, Endpoint, ServerConfig};
use rustls::pki_types::{CertificateDer, PrivatePkcs8KeyDer};
use sha2::{Digest, Sha256};
use std::{collections::HashMap, net::SocketAddr, sync::Arc, time::{Duration, Instant}};
use tokio::{net::UdpSocket, sync::Mutex};
const MAGIC: &[u8] = b"FC01";
const HEADER: usize = 36;
const MAX_DATAGRAM: usize = 1500;
const MAX_SESSIONS: usize = 64;

fn argument(args: &[String], index: usize) -> Result<&str> {
    args.get(index).map(String::as_str).context("missing argument")
}
fn token() -> Result<Vec<u8>> {
    let text = std::fs::read_to_string(std::env::var("RELAY_TOKEN_FILE")?)?;
    let value = hex::decode(text.trim())?;
    if value.len() != 32 { bail!("relay admission token must be 32 bytes"); }
    Ok(value)
}
fn admitted(packet: &[u8], token: &[u8]) -> bool {
    if packet.len() <= HEADER || packet.len() > MAX_DATAGRAM + HEADER || &packet[..4] != MAGIC { return false; }
    // Compare all token bytes. Phase 0 capability is a shared lab secret,
    // NOT production device authentication; it is exposed on the outer UDP wire.
    packet[4..HEADER].iter().zip(token).fold(0u8, |acc,(a,b)| acc | (a ^ b)) == 0
}
fn wrap(payload: &[u8], token: &[u8]) -> Vec<u8> {
    [MAGIC, token, payload].concat()
}

async fn gateway(bind: &str, cert: &str, key: &str) -> Result<()> {
    let cert = CertificateDer::from(std::fs::read(cert)?);
    let key = PrivatePkcs8KeyDer::from(std::fs::read(key)?);
    let config = ServerConfig::with_single_cert(vec![cert], key.into())?;
    let endpoint = Endpoint::server(config, bind.parse()?)?;
    eprintln!("gateway lab service ready; no public Internet egress implemented");
    while let Some(incoming) = endpoint.accept().await {
        tokio::spawn(async move {
            let result: Result<()> = async {
                let connection = incoming.await?;
                let (mut send, mut recv) = connection.accept_bi().await?;
                let mut request = [0u8; 1];
                recv.read_exact(&mut request).await?;
                if request != [1] { bail!("unsupported lab operation"); }
                // Fixed 16 MiB deterministic transfer, no arbitrary destination API.
                let block = vec![0x5au8; 65536];
                for _ in 0..256 {
                    send.write_all(&block).await?;
                    tokio::time::sleep(Duration::from_millis(40)).await;
                }
                send.finish()?;
                send.stopped().await?;
                Ok(())
            }.await;
            if result.is_err() { eprintln!("lab connection ended"); }
        });
    }
    Ok(())
}

async fn relay(bind: &str, destination: &str) -> Result<()> {
    let token = Arc::new(token()?);
    // Literal address only: no client-selected DNS or CONNECT command.
    let destination: SocketAddr = destination.parse()?;
    let listener = Arc::new(UdpSocket::bind(bind).await?);
    let sessions = Arc::new(Mutex::new(HashMap::<SocketAddr, (Arc<UdpSocket>, Instant)>::new()));
    let mut packet = vec![0; 65536];
    let mut quota_start = Instant::now();
    let mut quota = 0usize;
    loop {
        let (size, peer) = listener.recv_from(&mut packet).await?;
        if !admitted(&packet[..size], &token) { continue; }
        if quota_start.elapsed() >= Duration::from_secs(1) { quota_start = Instant::now(); quota = 0; }
        quota += size;
        if quota > 2_000_000 { continue; } // 16 Mbps ingress lab ceiling.
        let mut map = sessions.lock().await;
        map.retain(|_,(_,last)| last.elapsed() < Duration::from_secs(30));
        if !map.contains_key(&peer) {
            if map.len() >= MAX_SESSIONS { continue; }
            let uplink = Arc::new(UdpSocket::bind("0.0.0.0:0").await?);
            uplink.connect(destination).await?;
            map.insert(peer, (uplink.clone(), Instant::now()));
            let downstream = listener.clone();
            let secret = token.clone();
            tokio::spawn(async move {
                let mut buffer = [0u8; MAX_DATAGRAM];
                let mut epoch = Instant::now();
                let mut bytes = 0usize;
                loop {
                    let received = tokio::time::timeout(Duration::from_secs(30), uplink.recv(&mut buffer)).await;
                    let size = match received { Ok(Ok(n)) => n, _ => break };
                    if epoch.elapsed() >= Duration::from_secs(1) { epoch = Instant::now(); bytes = 0; }
                    bytes += size;
                    if bytes > 2_000_000 { continue; }
                    if downstream.send_to(&wrap(&buffer[..size], &secret), peer).await.is_err() { break; }
                }
            });
        }
        let (uplink, last) = map.get_mut(&peer).unwrap();
        *last = Instant::now();
        uplink.send(&packet[HEADER..size]).await?;
    }
}

async fn client(cert: &str, route_a: &str, route_b: &str) -> Result<()> {
    let secret = Arc::new(token()?);
    let routes: Vec<SocketAddr> = vec![route_a.parse()?, route_b.parse()?];
    let adapter = Arc::new(UdpSocket::bind("127.0.0.1:0").await?);
    let adapter_addr = adapter.local_addr()?;
    let upstream = Arc::new(UdpSocket::bind("0.0.0.0:0").await?);
    let local_peer = Arc::new(Mutex::new(None::<SocketAddr>));
    let last_reply = Arc::new(Mutex::new(Instant::now()));
    let path = Arc::new(Mutex::new(0usize));
    {
        let (adapter, upstream, local_peer, secret, path) =
            (adapter.clone(), upstream.clone(), local_peer.clone(), secret.clone(), path.clone());
        let routes = routes.clone();
        tokio::spawn(async move {
            let mut data = [0u8; MAX_DATAGRAM];
            loop {
                let (size, peer) = match adapter.recv_from(&mut data).await { Ok(v) => v, Err(_) => break };
                *local_peer.lock().await = Some(peer);
                let target = routes[*path.lock().await];
                let _ = upstream.send_to(&wrap(&data[..size], &secret), target).await;
            }
        });
    }
    {
        let (adapter, upstream, local_peer, secret, last_reply) =
            (adapter.clone(), upstream.clone(), local_peer.clone(), secret.clone(), last_reply.clone());
        let routes = routes.clone();
        tokio::spawn(async move {
            let mut data = [0u8; MAX_DATAGRAM + HEADER];
            loop {
                let (size, source) = match upstream.recv_from(&mut data).await { Ok(v) => v, Err(_) => break };
                if !routes.contains(&source) || !admitted(&data[..size], &secret) { continue; }
                *last_reply.lock().await = Instant::now();
                if let Some(peer) = *local_peer.lock().await {
                    let _ = adapter.send_to(&data[HEADER..size], peer).await;
                }
            }
        });
    }
    let switches = Arc::new(std::sync::atomic::AtomicUsize::new(0));
    {
        let (last_reply, path, switches) = (last_reply.clone(), path.clone(), switches.clone());
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_millis(250)).await;
                let mut last = last_reply.lock().await;
                if last.elapsed() > Duration::from_millis(1500) {
                    let mut selected = path.lock().await;
                    *selected = 1 - *selected;
                    *last = Instant::now();
                    switches.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                    eprintln!("path changed; keeping the existing QUIC connection");
                }
            }
        });
    }
    let mut roots = rustls::RootCertStore::empty();
    roots.add(CertificateDer::from(std::fs::read(cert)?))?;
    let mut endpoint = Endpoint::client("127.0.0.1:0".parse()?)?;
    endpoint.set_default_client_config(ClientConfig::with_root_certificates(Arc::new(roots))?);
    let connection = endpoint.connect(adapter_addr, "gateway.test")?.await?;
    let (mut send, mut recv) = connection.open_bi().await?;
    send.write_all(&[1]).await?;
    send.finish()?;
    let started = Instant::now();
    let data = tokio::time::timeout(Duration::from_secs(60), recv.read_to_end(16 * 1024 * 1024)).await??;
    if data.len() != 16 * 1024 * 1024 || data.iter().any(|x| *x != 0x5a) { bail!("transfer integrity failed"); }
    println!("{{\"bytes\":{},\"sha256\":\"{}\",\"seconds\":{:.3},\"path_switches\":{},\"quic_connections\":1}}",
        data.len(), hex::encode(Sha256::digest(&data)), started.elapsed().as_secs_f64(),
        switches.load(std::sync::atomic::Ordering::Relaxed));
    connection.close(0u32.into(), b"lab complete");
    endpoint.wait_idle().await;
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    rustls::crypto::ring::default_provider().install_default().ok();
    let args: Vec<String> = std::env::args().collect();
    match argument(&args, 1)? {
        "gateway" => gateway(argument(&args,2)?, argument(&args,3)?, argument(&args,4)?).await,
        "relay" => relay(argument(&args,2)?, argument(&args,3)?).await,
        "client" => client(argument(&args,2)?, argument(&args,3)?, argument(&args,4)?).await,
        _ => bail!("expected gateway|relay|client"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn malformed_and_unauthorized_packets_are_rejected() {
        let key = [7u8; 32];
        assert!(admitted(&wrap(b"encrypted-quic-packet", &key), &key));
        assert!(!admitted(&wrap(b"payload", &[8u8; 32]), &key));
        assert!(!admitted(b"CONNECT 8.8.8.8:443", &key));
        assert!(!admitted(&wrap(&vec![0; MAX_DATAGRAM+1], &key), &key));
        assert!(!admitted(&wrap(b"", &key), &key));
    }
}
