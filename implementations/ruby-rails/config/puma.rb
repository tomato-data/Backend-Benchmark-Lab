# 워커 수 (프로세스) - 각 워커는 독립 GVL
workers ENV.fetch("WEB_CONCURRENCY") { 2 }

# 스레드 수 (워커당) - I/O 대기 시 다른 스레드 실행
threads_count = ENV.fetch("RAILS_MAX_THREADS") { 5 }
threads threads_count, threads_count

# 포트 (다른 구현체와 동일하게 8000)
port ENV.fetch("PORT") { 8000 }

# 환경
environment ENV.fetch("RAILS_ENV") { "production" }

# 워커 부팅 시 DB 커넥션 재설정 (fork 후 필수)
before_worker_boot do
    ActiveRecord::Base.establish_connection
end

# 워커 간 메모리 공유
preload_app!
