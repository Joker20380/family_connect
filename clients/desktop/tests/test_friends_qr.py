import ctypes as c
import ctypes.util
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from friends_qr import invitation_matrix

@pytest.mark.parametrize('link',['', 'https://example.org/#'+'a'*64,
    'https://185.251.89.19:8443/invite/#'+'A'*64,
    'https://185.251.89.19:8443/invite/#'+'a'*64+'\x00extra'])
def test_invalid_link_rejected(link):
    with pytest.raises(ValueError):invitation_matrix(link)


def test_phone_decoder_recovers_exact_referral():
    if not ctypes.util.find_library('qrencode') or not ctypes.util.find_library('zbar'):
        pytest.skip('system QR encoder/independent decoder unavailable')
    url='https://185.251.89.19:8443/invite/#'+'0123456789abcdef'*4
    matrix=invitation_matrix(url);n=len(matrix);scale=5;size=(n+8)*scale
    pixels=bytes(0 if 4<=y//scale<n+4 and 4<=x//scale<n+4 and matrix[y//scale-4][x//scale-4] else 255 for y in range(size) for x in range(size))
    z=c.CDLL(ctypes.util.find_library('zbar'))
    signatures={
        'zbar_image_scanner_create':([],c.c_void_p),
        'zbar_image_create':([],c.c_void_p),
        'zbar_image_set_format':([c.c_void_p,c.c_ulong],None),
        'zbar_image_set_size':([c.c_void_p,c.c_uint,c.c_uint],None),
        'zbar_image_set_data':([c.c_void_p,c.c_void_p,c.c_ulong,c.c_void_p],None),
        'zbar_scan_image':([c.c_void_p,c.c_void_p],c.c_int),
        'zbar_image_first_symbol':([c.c_void_p],c.c_void_p),
        'zbar_symbol_get_data':([c.c_void_p],c.c_char_p),
        'zbar_image_destroy':([c.c_void_p],None),
        'zbar_image_scanner_destroy':([c.c_void_p],None)}
    for name,(args,result) in signatures.items():
        fn=getattr(z,name);fn.argtypes=args;fn.restype=result
    scanner=z.zbar_image_scanner_create();image=z.zbar_image_create()
    buffer=c.create_string_buffer(pixels)
    try:
        z.zbar_image_set_format(image,int.from_bytes(b'Y800','little'))
        z.zbar_image_set_size(image,size,size)
        z.zbar_image_set_data(image,buffer,len(pixels),None)
        assert z.zbar_scan_image(scanner,image)==1
        assert z.zbar_symbol_get_data(z.zbar_image_first_symbol(image)).decode()==url
    finally:
        z.zbar_image_destroy(image);z.zbar_image_scanner_destroy(scanner)
