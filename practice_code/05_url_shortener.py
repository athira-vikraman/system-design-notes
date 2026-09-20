"""
URL Shortener  ->  PRACTICE_PROBLEMS.md #1

The core of the problem is turning a number into a short code.

Base62 uses 0-9, a-z, A-Z = 62 characters.
    62^7 = about 3.5 trillion codes from 7 characters.

Why a counter instead of hashing the URL?
    A counter can never collide. Hashing can, so you would have to
    check the database every time and retry on a clash.
"""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(number):
    """12345 -> 'dnh'"""
    if number == 0:
        return ALPHABET[0]

    code = ""
    while number > 0:
        number, remainder = divmod(number, BASE)
        code = ALPHABET[remainder] + code
    return code


def decode(code):
    """'dnh' -> 12345"""
    number = 0
    for char in code:
        number = number * BASE + ALPHABET.index(char)
    return number


class URLShortener:
    """
    In production the counter lives in the database and each server
    takes a block of numbers (say 1000 at a time), so servers never
    hand out the same code.
    """

    def __init__(self, domain="short.ly", start=1_000_000):
        self.domain = domain
        self.counter = start
        self.code_to_url = {}
        self.url_to_code = {}   # so the same URL reuses its code
        self.clicks = {}

    def shorten(self, long_url, custom=None):
        if custom:
            if custom in self.code_to_url:
                raise ValueError(f"'{custom}' is already taken")
            code = custom
        elif long_url in self.url_to_code:
            return f"{self.domain}/{self.url_to_code[long_url]}"
        else:
            code = encode(self.counter)
            self.counter += 1

        self.code_to_url[code] = long_url
        self.url_to_code[long_url] = code
        self.clicks[code] = 0
        return f"{self.domain}/{code}"

    def resolve(self, short_url):
        code = short_url.rsplit("/", 1)[-1]
        if code not in self.code_to_url:
            return None
        self.clicks[code] += 1
        return self.code_to_url[code]


def demo():
    print("Base62 encoding\n")
    for n in [0, 61, 62, 12345, 1_000_000, 3_521_614_606_207]:
        code = encode(n)
        print(f"  {n:>15,}  ->  {code:<8}  (decodes back to {decode(code):,})")

    print(f"\n  7 characters gives {BASE**7:,} possible codes\n")

    print("Shortening URLs\n")
    service = URLShortener()

    urls = [
        "https://github.com/athira-vikraman/chromadb-semantic-search",
        "https://docs.trychroma.com/getting-started",
    ]
    for url in urls:
        short = service.shorten(url)
        print(f"  {short}")
        print(f"     -> {url}")

    print("\n  same URL again reuses the same code:")
    print(f"     {service.shorten(urls[0])}")

    print("\n  custom alias:")
    print(f"     {service.shorten('https://example.com/very/long/path', custom='mylink')}")

    print("\nResolving and counting clicks\n")
    for _ in range(3):
        service.resolve("short.ly/mylink")
    resolved = service.resolve("short.ly/mylink")
    print(f"  short.ly/mylink -> {resolved}")
    print(f"  clicks: {service.clicks['mylink']}")

    print(f"\n  unknown code -> {service.resolve('short.ly/nope')}")


if __name__ == "__main__":
    demo()
