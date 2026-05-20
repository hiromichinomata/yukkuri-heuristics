# python/ch01/rating_band.py
def rating_band(r: int) -> str:
    bands = [
        (400, "Gray"),
        (800, "Brown"),
        (1200, "Green"),
        (1600, "Cyan"),
        (2000, "Blue"),
        (2400, "Yellow"),
        (2800, "Orange"),
        (10**9, "Red"),
    ]
    for limit, name in bands:
        if r < limit:
            return name
    return "Red"


if __name__ == "__main__":
    for r in [0, 399, 800, 1500, 2100, 3000]:
        print(r, rating_band(r))
