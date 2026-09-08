use anyhow::{Context, Result};
use quinn::{ClientConfig, Connection, ServerConfig, TransportConfig};
use rustls::pki_types::{CertificateDer, PrivatePkcs8KeyDer};
use sha2::{Digest, Sha256};
use std::{path::PathBuf, sync::Arc, time::Duration};

pub fn local_pin() -> Result<String> { Ok(hex::encode(Sha256::digest(std::fs::read(directory().join("cert.der"))?))) }
fn directory() -> PathBuf { PathBuf::from(std::env::var("IDENTITY_DIR").unwrap_or("/identity".into())) }
fn certs() -> Result<Vec<CertificateDer<'static>>> { Ok(vec![CertificateDer::from(std::fs::read(directory().join("cert.der"))?)]) }
fn private() -> Result<rustls::pki_types::PrivateKeyDer<'static>> { Ok(PrivatePkcs8KeyDer::from(std::fs::read(directory().join("key.der"))?).into()) }
fn roots() -> Result<Arc<rustls::RootCertStore>> {
    let mut roots = rustls::RootCertStore::empty();
    roots.add(CertificateDer::from(std::fs::read("/trust/ca.der")?))?;
    Ok(Arc::new(roots))
}
fn transport(outer: bool) -> Arc<TransportConfig> {
    let mut t = TransportConfig::default();
    let mtu=if outer {1400} else {1200};
    t.initial_mtu(mtu).min_mtu(mtu).mtu_discovery_config(None);
    t.keep_alive_interval(Some(Duration::from_secs(1)));
    t.max_idle_timeout(Some(Duration::from_secs(10).try_into().unwrap()));
    t.max_concurrent_bidi_streams(1u32.into()).max_concurrent_uni_streams(0u32.into());
    t.datagram_receive_buffer_size(if outer {Some(128*1024)} else {None});
    Arc::new(t)
}
pub fn server(outer: bool) -> Result<ServerConfig> {
    let verifier=rustls::server::WebPkiClientVerifier::builder(roots()?).build()?;
    let mut crypto=rustls::ServerConfig::builder().with_client_cert_verifier(verifier).with_single_cert(certs()?,private()?)?;
    crypto.alpn_protocols=vec![if outer {b"fc-relay-v2".to_vec()} else {b"fc-gateway-v2".to_vec()}];
    // No 0-RTT application data; admission is checked after the authenticated handshake.
    crypto.max_early_data_size=0;
    let mut config=ServerConfig::with_crypto(Arc::new(quinn::crypto::rustls::QuicServerConfig::try_from(crypto)?));
    config.transport_config(transport(outer)); Ok(config)
}
pub fn client(outer: bool) -> Result<ClientConfig> {
    let mut crypto=rustls::ClientConfig::builder().with_root_certificates(roots()?).with_client_auth_cert(certs()?,private()?)?;
    crypto.alpn_protocols=vec![if outer {b"fc-relay-v2".to_vec()} else {b"fc-gateway-v2".to_vec()}];
    crypto.enable_early_data=false;
    let mut config=ClientConfig::new(Arc::new(quinn::crypto::rustls::QuicClientConfig::try_from(crypto)?));
    config.transport_config(transport(outer)); Ok(config)
}
pub fn peer_pin(connection: &Connection) -> Result<String> {
    let identity=connection.peer_identity().context("missing TLS identity")?;
    let chain=identity.downcast::<Vec<CertificateDer<'static>>>().map_err(|_| anyhow::anyhow!("invalid TLS identity"))?;
    Ok(hex::encode(Sha256::digest(chain.first().context("empty TLS chain")?.as_ref())))
}
