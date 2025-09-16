module.exports = {
    apps: [
        {
            name: 'miner-registration',
            script: 'app/utils/register.py',
            interpreter: './venv/bin/python',
            cwd: '/root/workspace/wallet_management_flask',
            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '1G',
            env: {
                NODE_ENV: 'production',
                PYTHONPATH: '/root/workspace/wallet_management_flask',
                PYTHONUNBUFFERED: '1',
                DATABASE_URL: 'postgresql://tao:btc2Moon@localhost',
                WALLET_MASTER_KEY: 'HJ8vYxgGv33TcdwGgdBgNqLW6EPb8cHLu2DwubCPtS0=',
                WALLET_PBKDF2_ITERATIONS: '100000'
            },
            error_file: './logs/pm2-error.log',
            out_file: './logs/pm2-out.log',
            log_file: './logs/pm2-combined.log',
            time: true,
            log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
            merge_logs: true,
            kill_timeout: 5000,
            restart_delay: 5000,
            max_restarts: 10,
            min_uptime: '10s'
        }
    ]
};
