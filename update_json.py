import time

from GetJson import REQUEST_DELAY, getAllCodes, getJson


def main():
    for code in getAllCodes():
        requested = getJson(code, False)
        requested = getJson(code, True) or requested
        if requested:
            time.sleep(REQUEST_DELAY)


if __name__ == '__main__':
    main()
