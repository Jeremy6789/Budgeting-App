import os
import subprocess

# 設定你的 GitHub 網址
GITHUB_URL = "https://github.com/Jeremy6789/Budgeting-App.git"

def run_command(command):
    """執行終端機指令並顯示結果"""
    print(f"正在執行: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 錯誤: {result.stderr}")
    else:
        print(f"✅ 成功: {result.stdout}")

def main():
    # 1. 自動產生 .gitignore (防止上傳垃圾檔案)
    print("--- 1. 檢查 .gitignore ---")
    gitignore_content = "venv/\n__pycache__/\ndata.json\n.DS_Store\n*.pyc\n"
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    print("✅ .gitignore 已更新")

    # 2. 自動產生 requirements.txt (為了與人協作)
    print("\n--- 2. 產生 requirements.txt ---")
    run_command("pip freeze > requirements.txt")

    # 3. Git 初始化與連接
    print("\n--- 3. Git 初始化 ---")
    if not os.path.exists(".git"):
        run_command("git init")
        run_command(f"git remote add origin {GITHUB_URL}")
    else:
        # 如果已經有 git，確保遠端網址正確
        run_command(f"git remote set-url origin {GITHUB_URL}")

    # 4. 提交與上傳
    print("\n--- 4. 上傳到 GitHub ---")
    run_command("git add .")
    commit_msg = input("請輸入這次更新的說明 (例如: 修改了介面): ")
    if not commit_msg:
        commit_msg = "Update Budgeting App"
    
    run_command(f'git commit -m "{commit_msg}"')
    run_command("git branch -M main")
    
    print("\n🚀 正在推送到 GitHub，請稍候...")
    # 使用 push -u 確保分支對接
    run_command("git push -u origin main")

    print("\n✨ 全部完成！去 GitHub 網頁看看吧：")
    print(GITHUB_URL)

if __name__ == "__main__":
    main()