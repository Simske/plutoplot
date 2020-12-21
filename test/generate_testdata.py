def generate_gridfile(filename="grid.out", dims=(10, 9, 8)):
    with open(filename, "w") as f:
        f.write("# FILE HEADER\n")

        for res in dims:
            f.write(f"{res}\n")
            for i in range(res):
                f.write(f" {i}   {i:.12e}    {i+1:.12e}\n")


if __name__ == "__main__":
    generate_gridfile()
