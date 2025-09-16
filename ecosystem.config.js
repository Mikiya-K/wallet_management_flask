module.exports = {
    apps: [
        {
            name: 'wallet-management-flask',
            script: './venv/bin/gunicorn',
            args: [
                '-w', '4',
                '-k', 'sync',
                '-b', '0.0.0.0:16003',
                '--timeout', '300',
                '--max-requests', '1000',
                '--max-requests-jitter', '100',
                '--preload',
                '--access-logfile', 'logs/gunicorn-access.log',
                '--error-logfile', 'logs/gunicorn-error.log',
                '--log-level', 'info',
                '--enable-stdio-inheritance',
                'wsgi:app'
            ],
            interpreter: './venv/bin/python',
            cwd: '/root/workspace/wallet_management_flask',
            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '2G',
            env: {
                PYTHONPATH: '/root/workspace/wallet_management_flask',
                PYTHONUNBUFFERED: '1'
            },
            env_file: '.env',
            error_file: './logs/flask-error.log',
            out_file: './logs/flask-out.log',
            log_file: './logs/flask-combined.log',
            time: true,
            log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
            merge_logs: true,
            kill_timeout: 10000,
            restart_delay: 3000,
            max_restarts: 10,
            min_uptime: '30s'
        },
        {
            name: 'miner-register',
            script: 'app/utils/register.py',
            interpreter: './venv/bin/python',
            cwd: '/root/workspace/wallet_management_flask',
            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '1G',
            env: {
                PYTHONPATH: '/root/workspace/wallet_management_flask',
                PYTHONUNBUFFERED: '1'
            },
            env_file: '.env',
            error_file: './logs/register-error.log',
            out_file: './logs/register-out.log',
            log_file: './logs/register-combined.log',
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
