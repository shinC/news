import os
import time
import subprocess
from datetime import datetime, timezone, timedelta

# KST (UTC+9) 설정
KST = timezone(timedelta(hours=9))

def run_command(cmd_list):
    """지정된 커맨드를 실행하고 로그를 출력합니다."""
    print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] 실행 시작: {' '.join(cmd_list)}")
    try:
        # PYTHONPATH 설정을 유지하여 실행
        env = os.environ.copy()
        env["PYTHONPATH"] = env.get("PYTHONPATH", "") + ":" + os.getcwd()
        
        res = subprocess.run(cmd_list, env=env, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] 성공적으로 완료되었습니다.")
        else:
            print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] 에러 발생 (코드 {res.returncode}):")
            print(res.stderr)
    except Exception as e:
        print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] 실행 중 예외 발생: {e}")

def main():
    print(f"=== 로컬 경제뉴스 자동화 스케줄러 시작 (KST 기준 작동) ===")
    
    # 상태 플래그
    last_reset_date = None
    main_scraped_today = False
    last_macro_run_time = None
    
    while True:
        now = datetime.now(KST)
        today_str = now.strftime('%Y-%m-%d')
        weekday = now.weekday() # 0: 월요일 ~ 6: 일요일
        
        # 1. 자정이 지나면 일일 실행 플래그 리셋
        if last_reset_date != today_str:
            main_scraped_today = False
            last_macro_run_time = None
            last_reset_date = today_str
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 일일 스케줄 플래그 초기화 완료 (요일: {weekday})")
            
        # 평일(월~금)에만 스크래핑 스케줄 작동
        if weekday < 5:
            current_time_str = now.strftime('%H:%M')
            hour = now.hour
            minute = now.minute
            
            # A. 15:32 한국 주요 지수 및 특징주 1차 수집 (main_kr.py)
            if not main_scraped_today and current_time_str == "15:32":
                run_command(["python", "src/main_kr.py"])
                main_scraped_today = True
                
            # B. 15:50 ~ 16:50 사이 10분 간격으로 마감 뉴스 추가 스크래핑 (run_macro_closing.py)
            in_macro_window = (hour == 15 and minute >= 50) or (hour == 16 and minute <= 50)
            if in_macro_window:
                should_run_macro = False
                if last_macro_run_time is None:
                    should_run_macro = True
                else:
                    elapsed = (now - last_macro_run_time).total_seconds()
                    if elapsed >= 580: # 약 10분(600초) 간격 (미세 오차 보정 위해 580초로 필터링)
                        should_run_macro = True
                        
                if should_run_macro:
                    run_command(["python", "src/run_macro_closing.py"])
                    last_macro_run_time = now
                    
        # 30초 대기 후 다음 루프 감시
        time.sleep(30)

if __name__ == "__main__":
    main()
