//! Bounded WireGuard datagram framing over one authenticated inner QUIC stream.
//! Only the gateway may connect to its fixed, loopback WireGuard service.
use anyhow::{bail, Result};
use quinn::{RecvStream, SendStream};
use tokio::{io::AsyncReadExt, net::UdpSocket};

const MAX_PACKET: usize = 2048;

async fn read_packet<R: tokio::io::AsyncRead + Unpin>(input: &mut R) -> Result<Vec<u8>> {
    let size = input.read_u16().await? as usize;
    if size == 0 || size > MAX_PACKET { bail!("invalid packet length"); }
    let mut packet = vec![0; size];
    input.read_exact(&mut packet).await?;
    Ok(packet)
}

pub async fn bridge(mut send: SendStream, mut recv: RecvStream, udp: UdpSocket) -> Result<()> {
    // Separate futures: cancelling a partial framed read on UDP arrival would desynchronise it.
    let upload = async {
        let mut packet = [0u8; MAX_PACKET + 1];
        loop {
            let size = udp.recv(&mut packet).await?;
            if size == 0 || size > MAX_PACKET { continue; }
            send.write_all(&(size as u16).to_be_bytes()).await?;
            send.write_all(&packet[..size]).await?;
        }
        #[allow(unreachable_code)] Ok::<(), anyhow::Error>(())
    };
    let download = async {
        loop {
            let packet = read_packet(&mut recv).await?;
            udp.send(&packet).await?;
        }
        #[allow(unreachable_code)] Ok::<(), anyhow::Error>(())
    };
    tokio::select! { result = upload => result, result = download => result }
}

pub async fn gateway(send: SendStream, recv: RecvStream) -> Result<()> {
    if std::env::var("ENABLE_PACKET_GATEWAY").as_deref() != Ok("1") {
        bail!("packet gateway disabled");
    }
    let udp = UdpSocket::bind("127.0.0.1:0").await?;
    // No endpoint is accepted from clients, even authenticated ones.
    udp.connect("127.0.0.1:51820").await?;
    bridge(send, recv, udp).await
}

pub async fn client(mut send: SendStream, mut recv: RecvStream) -> Result<()> {
    send.write_all(&[2]).await?;
    let mut ready = [0];
    recv.read_exact(&mut ready).await?;
    if ready != [2] { bail!("packet gateway refused"); }
    let udp = UdpSocket::bind("127.0.0.1:51821").await?;
    // The local kernel WireGuard interface has a fixed source port.
    udp.connect("127.0.0.1:51822").await?;
    eprintln!("packet tunnel ready; inner_quic_connections=1");
    bridge(send, recv, udp).await
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::io::AsyncWriteExt;

    #[tokio::test]
    async fn rejects_zero_oversize_and_truncated_frames() {
        for bytes in [vec![0,0],vec![8,1],vec![0,2,1]] {
            assert!(read_packet(&mut bytes.as_slice()).await.is_err());
        }
    }

    #[tokio::test]
    async fn fragmented_frames_preserve_boundaries() {
        let (mut tx, mut rx) = tokio::io::duplex(2);
        let writer = tokio::spawn(async move {
            for byte in [0,3,1,2,3,0,1,4] { tx.write_all(&[byte]).await.unwrap(); }
        });
        assert_eq!(read_packet(&mut rx).await.unwrap(), vec![1,2,3]);
        assert_eq!(read_packet(&mut rx).await.unwrap(), vec![4]);
        writer.await.unwrap();
    }
}
