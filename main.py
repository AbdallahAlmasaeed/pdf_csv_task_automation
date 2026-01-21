import os
import pandas as pd
import pdfplumber


def read_csv(path):
    df = pd.read_csv(path)
    print(f"CSV loaded: {df.shape[0]} rows x {df.shape[1]} columns")
    print("Columns:", ", ".join(df.columns))
    return df


def read_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    print(f"PDF loaded: {len(text)} characters")
    return text


def do_task(df_or_text, task):
    task = task.lower()

    # CSV tasks
    if isinstance(df_or_text, pd.DataFrame):
        if "highest salary" in task:
            if "Salary" in df_or_text.columns:
                row = df_or_text[df_or_text["Salary"] == df_or_text["Salary"].max()]
                print("\nHighest Salary Row(s):")
                print(row)
                return
        if "lowest age" in task:
            if "Age" in df_or_text.columns:
                row = df_or_text[df_or_text["Age"] == df_or_text["Age"].min()]
                print("\nLowest Age Row(s):")
                print(row)
                return
        if "sum salary" in task:
            if "Salary" in df_or_text.columns:
                total = df_or_text["Salary"].sum()
                print("\nSum of Salary:", total)
                return
        print("Task not recognized or column missing.")

    # PDF tasks (just basic search)
    elif isinstance(df_or_text, str):
        if "find" in task:
            keyword = task.replace("find", "").strip()
            lines = [line for line in df_or_text.split("\n") if keyword.lower() in line.lower()]
            print(f"\nLines containing '{keyword}':")
            for l in lines:
                print("-", l)
            return
        print("Task not recognized for PDF.")


def main():
    print("=== Standalone PDF/CSV Processor ===")

    # Step 1: ask for file path
    while True:
        path = input("Enter file path (CSV or PDF) or 'exit': ").strip()
        if path.lower() == "exit":
            print("Goodbye!")
            return
        if not os.path.exists(path):
            print("File not found. Try again.")
            continue
        if path.lower().endswith(".csv"):
            data = read_csv(path)
        elif path.lower().endswith(".pdf"):
            data = read_pdf(path)
        else:
            print("Unsupported file type. Only CSV or PDF allowed.")
            continue
        break

    # Step 2: ask for tasks repeatedly
    while True:
        task = input("\nEnter task (or type 'exit' to quit): ").strip()
        if task.lower() in {"exit", "quit"}:
            print("Exiting tasks. Goodbye!")
            break
        do_task(data, task)


if __name__ == "__main__":
    main()
