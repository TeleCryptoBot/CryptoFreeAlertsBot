def format_number(n: float) -> str:
    symbols = ('', 'K', 'M', 'B', 'T', 'P', 'E')
    magnitude = 0
    while abs(n) >= 1000 and magnitude < len(symbols) - 1:
        magnitude += 1
        n /= 1000.0
    return f"{n:,.2f} {symbols[magnitude]}"
