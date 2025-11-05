from src.modules.initialize import Initialize

path = r"C:\Users\Balaji\Documents\sta.pdf"
pdfs = Initialize(path=path)
print("Starting page analysis...")
pdfs.analyze_page(chuck=300,over=3)

while True:
    q = input("You : ")
    if q.lower() == 'exit' or q.lower()=='quit':
        break

    print("AI  : ",end="")
    for ch in pdfs.query(q,10):
        print(ch,end="",flush=True)
    print('\n\n')