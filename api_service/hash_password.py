# hash_password.py
import sys
from argon2 import PasswordHasher

def gen_hash(plain: str) -> str:
    ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32)
    return ph.hash(plain)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hash_password.py <plain_password>")
        sys.exit(1)
    pw = sys.argv[1]
    print(gen_hash(pw))
