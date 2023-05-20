# btwifi

A bluetooth interface for setting wifi on embedding devices.

## Setting up the environment

1. Install python3
 <!--  mark down link to `` -->
2. Install bless library for python3 (`sudo pip3 install bless dbus_next`)[https://github.com/kevincar/bless]
3. (Optional) Set up Systemd service for the script

    - `sudo nano /etc/systemd/system/btwifi.service`

    ```
        [Unit]
        Description=btwifi

        [Service]
        ExecStart=/usr/bin/python3 /<path-to-this-directory>/main.py
        Restart=always
        User=root
        Environment=PYTHONUNBUFFERED=1

        [Install]
        WantedBy=multi-user.target
    ```

    - `sudo systemctl daemon-reload`
    - `sudo systemctl enable btwifi.service`
    - `sudo systemctl start btwifi.service`
