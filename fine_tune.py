import asyncio
import subprocess
import os
import time
import sys
from dotenv import load_dotenv

#使用ファイル(拡張子なし)
input_file_name = "qa_list"
extension = ".jsonl"

#初期化関数
def init():
    global log_file,input_file_name,OPENAI_API_KEY
    # logを格納するファイル
    log_file = "log.txt"
    # 使用するfile_nameを定義

    # ファイルがない場合は初期化、ある場合は中の記述をclearする
    with open(log_file, "w") as file:
        file.write("")
    print("log_fileを初期化しました。")

    # .envを取得
    load_dotenv()
    print(".envを取得しました。")

    # os.environを用いて環境変数を取得 
    OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
    # print("API_KEY :" + OPENAI_API_KEY + " で実行します。")

    # OPENAI_API_KEYをexport
    subprocess.run("export OPENAI_API_KEY=" + OPENAI_API_KEY, shell=True)
    print("コマンド: export OPENAI_API_KEY=" + OPENAI_API_KEY + "を実行しました")

#事前準備処理
async def prepare():
    prepare = subprocess.run(f"openai tools fine_tunes.prepare_data -f {input_file_name}{extension} -q", shell=True, capture_output=True, text=True)
    print("ファイルの準備が完了しました。")

    #ログの書き込み
    with open(log_file, "a") as file:
        file.write(prepare.stdout)

    print("log_fileを更新しました。")

#fine-tuning作成処理
async def create():
    global last_command

    # fine_tuningするファイル名
    print(f"fine_tuningを開始します。ファイル名: {input_file_name}_prepared{extension} ")
    create = subprocess.run(f"echo | openai api fine_tunes.create -t {input_file_name}_prepared{extension} -m davinci", shell=True, capture_output=True, text=True)
    
    #ログの最後に記述されているコマンドを取得
    last_command = create.stdout.splitlines()[-2].strip()

    print("コマンド: " + last_command + "を取得しました")

    #ログの書き込み
    with open(log_file, "a") as file:
        file.write(create.stdout)

    print("log_fileを更新しました。")
    print(
        f"コマンド: openai api fine_tunes.create -t {input_file_name}_prepared{extension} -m davinci は正常に終了しました。")

#続行処理
async def follow():
    print(f"このコマンドで続行します:  {last_command}")
    global output
    output = subprocess.run("echo |" + last_command,
                            shell=True, capture_output=True, text=True)
    
    #ログの書き込み
    with open(log_file, "a") as file:
        file.write(output.stdout)

    print("log_fileを更新しました。")
    print(f"{last_command} は正常に終了しました。")

#成功した場合の処理
async def succeed():
    print("成功を示す文字列が見つかりました。ループを終了します。")

    #ログの書き込み
    with open(log_file, "a") as file:
        file.write(output.stdout)
    print("log_fileを更新しました。")
    
    #ログの取得
    with open(log_file, "r") as file:
        contents = file.read()

    #davinci_keyの取得
    model_name = contents.splitlines()[-1].strip().split()[4]
    print("davinci_keyを取得しました。")    

    print(f"生成されたモデル名{model_name}")

#本編
async def main():
    try:
        init()
        await asyncio.wait_for(prepare(), timeout=5)
        await asyncio.wait_for(create(), timeout=300)

        #ログの"openai"の文字列が入っていればループに入る
        if "openai" in last_command:
            while True:
                # タスク開始時刻を記録
                start_time = time.time()  

                await asyncio.wait_for(follow(), timeout=300)

                # タスク終了時刻を記録
                end_time = time.time()  

                # タスクの実行時間を計算
                execution_time = end_time - start_time  
                
                #followが1秒以内に終わる場合はエラーが発生しているとみなす（無限ループの回避）
                if execution_time < 1:
                    print("ループエラーが発生しました。再度実行してください。")
                    break

                #ログの"succeeded"の文字列が入っている場合はループを終了する
                if "succeeded" in output.stdout:
                    await asyncio.wait_for(succeed(), timeout=3)
                    break
        
        else:
            print("予期せぬエラーが発生しました。再度実行してください。")
            sys.exit()

    #タイムアウトした場合は例外処理として扱う
    except asyncio.TimeoutError:
        print("タイムアウトエラーが発生しました。再度実行してください。")

asyncio.run(main())
