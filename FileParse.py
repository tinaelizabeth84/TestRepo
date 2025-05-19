
filePath1 = "/Users/teliza268/Documents/PythonLearn/ParseFile.txt"
filePath2 = "/Users/teliza268/Documents/PythonLearn/ComponentVersion.csv"

try:
    f1 = open(filePath1)
    for line in f1:
        line = line.strip()
        print(line)
        component = line.split()[0]
        version = line.split()[1]
        print(component)
        print(version)
        f2 = open(filePath2,'a')
        stringToWrite = "{} {}\n".format(component,version)
        f2.write(stringToWrite)
        f2.close()

        # Process the line
finally:
    f1.close()