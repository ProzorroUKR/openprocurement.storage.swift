# gevent must patch ssl/socket before swiftclient imports them, otherwise
# documentservice's monkey.patch_all() at import time blows the stack.
from gevent import monkey

monkey.patch_all()
