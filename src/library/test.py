class myList:
    def __init__(self, ls: list[int]) -> None:
        self.ls = ls
        self.idx = -1

    def __iter__(self):
        return self

    def __next__(self):
        self.idx += 1
        if self.idx >= len(self.ls):
            raise StopIteration
        return self.ls[self.idx]


class Runner:
    def __init__(self, ls: myList) -> None:
        self.ls = ls

    def run(self) -> None:
        for x in self.ls:
            self.print_current_status()

    def print_current_status(self) -> None:
        print(self.ls.idx)


if __name__ == "__main__":
    ls = myList([1, 2, 3, 4, 5])
    runner = Runner(ls)
    runner.run()
