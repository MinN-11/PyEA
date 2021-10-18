
from typing import *

ASSET_TYPES: Dict[str, Union[None, Callable[[bytes], bytes]]] = {".dmp": None}

