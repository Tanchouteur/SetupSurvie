"""Rebuild the tiny, fictional browser map (never real OSM data).

Optional generator only: uv run --with pmtiles==3.7.0 tests/make_map_display_fixture.py
The committed archive is used without installing pmtiles in the application/CI.
"""
import gzip
import math
from pathlib import Path
from pmtiles.writer import Writer
from pmtiles.tile import Compression, TileType, zxy_to_tileid


def varint(value):
    result=bytearray()
    while value>127:result.append((value&127)|128);value>>=7
    result.append(value);return bytes(result)


def field(number,value):
    return varint(number*8+2)+varint(len(value))+value if isinstance(value,bytes) else varint(number*8)+varint(value)


def feature(kind, positions, props):
    keys=list(props);values=list(props.values())
    commands=[];last_x=last_y=0
    for i,(x,y) in enumerate(positions):
        commands.extend([9 if i==0 else 10,((x-last_x)<<1)^((x-last_x)>>31),((y-last_y)<<1)^((y-last_y)>>31)])
        last_x,last_y=x,y
    if kind==3:commands.append(15)
    return (field(2,b''.join(varint(v) for i in range(len(keys)) for v in (i,i)))+field(3,kind)
            +field(4,b''.join(varint(v) for v in commands)))


def layer(name,kind,positions,props):
    data=field(15,2)+field(1,name.encode())+field(2,feature(kind,positions,props))
    for key in props:data+=field(3,key.encode())
    for value in props.values():data+=field(4,field(1,value.encode()))
    return field(3,data+field(5,4096))


def main():
    target=Path(__file__).resolve().parents[1]/'fixtures/maps/display-small.pmtiles'
    z=12;x=int((6.1+180)/360*2**z);y=int((1-math.asinh(math.tan(math.radians(43.1)))/math.pi)/2*2**z)
    tile=layer('earth',3,[(0,0),(4096,0),(4096,4096),(0,4096)],{})
    tile+=layer('landcover',3,[(100,100),(1800,100),(1800,3900),(100,3900)],{})
    tile+=layer('water',3,[(3100,600),(3800,600),(3800,2300),(3100,2300)],{})
    tile+=layer('roads',2,[(100,3000),(2000,2000),(4000,1900)],{'name':'Chemin fictif','kind':'path'})
    tile+=layer('places',1,[(2200,1700)],{'name':'Village de test'})
    tile+=layer('buildings',3,[(1900,2100),(2050,2100),(2050,2250),(1900,2250)],{})
    # PMTiles writer uses gzip internally; freeze timestamps for reproducibility.
    compress=gzip.compress;gzip.compress=lambda raw,*args,**kwargs:compress(raw,mtime=0)
    with target.open('wb') as stream:
        writer=Writer(stream);writer.write_tile(zxy_to_tileid(z,x,y),tile)
        writer.finalize({'tile_compression':Compression.NONE,'tile_type':TileType.MVT,
                         'min_lon_e7':60000000,'max_lon_e7':62000000,'min_lat_e7':430000000,'max_lat_e7':432000000,
                         'center_lon_e7':61000000,'center_lat_e7':431000000,'center_zoom':12},
                        {'name':'Fictional test only','vector_layers':[{'id':name,'fields':{}} for name in ['earth','landcover','water','roads','places','buildings']]})
    print(target.name,target.stat().st_size)


if __name__=='__main__':main()
