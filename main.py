from MedianStream import MedianStream

def main():
    stream = MedianStream()

    '''
    For testing, I use a static array
    but data should be generated in real time
    '''
    data = [5, 2, 8, 3, 10]

    for num in data:
        stream.add_number(num)
        median = stream.get_median()
        print(f"insert {num}, median = {median}")

if __name__ == "__main__":
    main()