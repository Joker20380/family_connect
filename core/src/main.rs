//! Authenticated, catalog-discovered Phase 0 laboratory; no public egress.
mod discovery;
mod tls;
use anyhow::{bail, Context, Result};
use discovery::{Discovery, Node};
use quinn::{Connection, Endpoint};
use sha2::{Digest, Sha256};
use std::{net::SocketAddr, sync::{Arc, atomic::{AtomicUsize, Ordering}}, time::{Duration, Instant}};
use tokio::{net::UdpSocket, sync::{Mutex, Semaphore}};

async fn monitor(connection: Connection, discovery: Arc<Discovery>, own: Node, device_pin: String) {
    loop {
        tokio::select! {
            _=connection.closed()=>return,
            _=tokio::time::sleep(Duration::from_secs(1))=>{
                let state=discovery.state.read().await;
                if !state.device_allowed(&device_pin) || state.node(&own.name,&own.role).map(|n|n.cert_sha256 != own.cert_sha256).unwrap_or(true) {
                    eprintln!("authorization lease ended");
                    connection.close(1u32.into(),b"authorization lease ended"); return;
                }
            }
        }
    }
}
async fn authorized(incoming: quinn::Incoming, discovery: &Arc<Discovery>) -> Result<(Connection,String)> {
    let connection=tokio::time::timeout(Duration::from_secs(5), incoming).await??;
    let pin=tls::peer_pin(&connection)?;
    if !discovery.state.read().await.device_allowed(&pin) {
        connection.close(2u32.into(),b"device not authorized"); bail!("device not authorized");
    }
    Ok((connection,pin))
}
async fn server(role: &str, name: &str, discovery: Arc<Discovery>) -> Result<()> {
    let own=discovery.state.read().await.node(name,role)?;
    if own.cert_sha256 != tls::local_pin()? { bail!("local certificate does not match signed identity"); }
    let endpoint=Endpoint::server(tls::server(role=="relay")?, own.endpoint)?;
    let slots=Arc::new(Semaphore::new(64));
    eprintln!("authenticated lab node ready");
    while let Some(incoming)=endpoint.accept().await {
        let permit=match slots.clone().try_acquire_owned() { Ok(p)=>p,Err(_)=>{incoming.refuse();continue;} };
        let (discovery,own)=(discovery.clone(),own.clone());
        let relay=role=="relay";
        tokio::spawn(async move {
            let _permit=permit;
            let result:Result<()>=async {
                let (connection,pin)=authorized(incoming,&discovery).await?;
                let watcher=tokio::spawn(monitor(connection.clone(),discovery.clone(),own,pin));
                let result=if relay {relay_session(connection.clone(),discovery).await} else {gateway_session(connection.clone()).await};
                watcher.abort(); connection.close(0u32.into(),b"session ended"); result
            }.await;
            if result.is_err() {eprintln!("connection rejected or ended");}
        });
    }
    Ok(())
}
async fn gateway_session(connection: Connection) -> Result<()> {
    let (mut send,mut recv)=connection.accept_bi().await?;
    let mut request=[0u8;1]; recv.read_exact(&mut request).await?;
    if request != [1] {bail!("unsupported lab operation");}
    let block=vec![0x5au8;65536];
    for _ in 0..256 {send.write_all(&block).await?;tokio::time::sleep(Duration::from_millis(40)).await;}
    send.finish()?; send.stopped().await?; Ok(())
}
async fn relay_session(connection: Connection, discovery: Arc<Discovery>) -> Result<()> {
    // Only operator configuration selects an identity; packets contain NO address.
    let gateway_name=std::env::var("GATEWAY_NAME")?;
    let target=discovery.state.read().await.node(&gateway_name,"gateway")?;
    let udp=UdpSocket::bind("0.0.0.0:0").await?;
    udp.connect(target.endpoint).await?;
    let mut bytes=[0u8;1500];
    let mut interval=tokio::time::interval(Duration::from_secs(1));
    let mut budget=4_000_000usize;
    loop {
        tokio::select! {
            _=interval.tick()=>{
                budget=4_000_000;
                let valid=discovery.state.read().await.node(&gateway_name,"gateway")?;
                if valid.identity != target.identity || valid.endpoint != target.endpoint || valid.cert_sha256 != target.cert_sha256 {bail!("gateway assignment changed");}
            },
            _=connection.closed()=>break,
            received=connection.read_datagram()=>{
                let data=received?;
                if data.is_empty() || data.len()>1200 || data.len()>budget {continue;}
                budget-=data.len(); udp.send(&data).await?;
            },
            received=udp.recv(&mut bytes)=>{
                let n=received?;
                if n>1200 || n>budget {continue;}
                budget-=n; connection.send_datagram(bytes[..n].to_vec().into())?;
            }
        }
    }
    Ok(())
}
async fn connect_node(endpoint: &Endpoint,node: &Node) -> Result<Connection> {
    let connection=tokio::time::timeout(Duration::from_secs(5),endpoint.connect(node.endpoint,&node.server_name)?).await??;
    if tls::peer_pin(&connection)? != node.cert_sha256 {
        connection.close(3u32.into(),b"node pin mismatch"); bail!("signed node certificate mismatch");
    }
    Ok(connection)
}
async fn client(discovery: Arc<Discovery>, probe: bool) -> Result<()> {
    let state=discovery.state.read().await.clone();
    let gateway=state.node("gateway-lab","gateway")?;
    let mut endpoint=Endpoint::client("0.0.0.0:0".parse()?)?;
    endpoint.set_default_client_config(tls::client(true)?);
    let mut paths=Vec::new();
    for node in state.nodes.iter().filter(|n|n.role=="relay") {
        if let Ok(connection)=connect_node(&endpoint,node).await {paths.push((node.clone(),connection));}
    }
    if paths.is_empty() {bail!("no authenticated relay available");}
    if probe {
        // A CA-issued but unlisted device must be closed by the RELAY, not
        // merely rejected by a client-side self-check.
        let reason=tokio::time::timeout(Duration::from_secs(4),paths[0].1.closed()).await?;
        println!("unauthorized peer closed: {reason}"); return Ok(());
    }
    let local_pin=tls::local_pin()?;
    if !state.device_allowed(&local_pin) {bail!("local device not authorized");}
    for (node, connection) in &paths {
        tokio::spawn(monitor(connection.clone(), discovery.clone(), node.clone(), local_pin.clone()));
    }
    let paths=Arc::new(paths);
    let adapter=Arc::new(UdpSocket::bind("127.0.0.1:0").await?);
    let adapter_address=adapter.local_addr()?;
    let peer=Arc::new(Mutex::new(None::<SocketAddr>));
    let last_reply=Arc::new(Mutex::new(Instant::now()));
    let selected=Arc::new(AtomicUsize::new(0));
    let switches=Arc::new(AtomicUsize::new(0));
    for (_,connection) in paths.iter() {
        let (connection,adapter,peer,last_reply)=(connection.clone(),adapter.clone(),peer.clone(),last_reply.clone());
        tokio::spawn(async move {
            while let Ok(bytes)=connection.read_datagram().await {
                *last_reply.lock().await=Instant::now();
                if let Some(address)=*peer.lock().await {let _=adapter.send_to(&bytes,address).await;}
            }
        });
    }
    {
        let (adapter,peer,paths,selected)=(adapter.clone(),peer.clone(),paths.clone(),selected.clone());
        tokio::spawn(async move {
            let mut bytes=[0u8;1500];
            while let Ok((n,address))=adapter.recv_from(&mut bytes).await {
                *peer.lock().await=Some(address);
                let _=paths[selected.load(Ordering::Relaxed)].1.send_datagram(bytes[..n].to_vec().into());
            }
        });
    }
    {
        let (paths,selected,switches,last_reply)=(paths.clone(),selected.clone(),switches.clone(),last_reply.clone());
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_millis(250)).await;
                let mut last=last_reply.lock().await;
                if paths.len()>1 && last.elapsed()>Duration::from_millis(1500) {
                    selected.store((selected.load(Ordering::Relaxed)+1)%paths.len(),Ordering::Relaxed);
                    *last=Instant::now();switches.fetch_add(1,Ordering::Relaxed);
                    eprintln!("authenticated relay path changed; inner session retained");
                }
            }
        });
    }
    let mut inner=Endpoint::client("127.0.0.1:0".parse()?)?;
    inner.set_default_client_config(tls::client(false)?);
    let connection=inner.connect(adapter_address,&gateway.server_name)?.await?;
    if tls::peer_pin(&connection)? != gateway.cert_sha256 {bail!("gateway pin mismatch");}
    // Catalog revocation also closes the client side; refreshing discovery is
    // independent of traffic and never exposes the device private key.
    let watcher=tokio::spawn(monitor(connection.clone(),discovery.clone(),gateway,local_pin));
    let (mut send,mut recv)=connection.open_bi().await?;
    send.write_all(&[1]).await?; send.finish()?;
    let started=Instant::now();
    let data=tokio::time::timeout(Duration::from_secs(60),recv.read_to_end(16*1024*1024)).await??;
    if data.len()!=16*1024*1024 || data.iter().any(|x|*x!=0x5a) {bail!("transfer integrity failed");}
    println!("{{\"bytes\":{},\"sha256\":\"{}\",\"seconds\":{:.3},\"path_switches\":{},\"quic_connections\":1,\"mutual_tls\":true,\"catalog_epoch\":{}}}",
        data.len(),hex::encode(Sha256::digest(&data)),started.elapsed().as_secs_f64(),switches.load(Ordering::Relaxed),state.epoch);
    watcher.abort();connection.close(0u32.into(),b"complete");inner.wait_idle().await;
    Ok(())
}
#[tokio::main]
async fn main()->Result<()> {
    rustls::crypto::ring::default_provider().install_default().ok();
    let args:Vec<String>=std::env::args().collect();
    let discovery=Discovery::start().await?;
    match args.get(1).map(String::as_str) {
        Some("gateway")=>server("gateway",args.get(2).context("node name required")?,discovery).await,
        Some("relay")=>server("relay",args.get(2).context("node name required")?,discovery).await,
        Some("client")=>client(discovery,false).await,
        Some("probe-relay")=>client(discovery,true).await,
        Some("verify-state")=>{println!("verified catalog epoch {}",discovery.state.read().await.epoch);Ok(())},
        _=>bail!("expected gateway|relay|client|probe-relay|verify-state")
    }
}
