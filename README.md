
# PI-Remote-HID

## Description

Connect a Raspberry Pi zero W to another computer.
The Pi will act as a keyboard that you'll be able to control remotely using [Ducky Scripts](https://www.hak5.org/gear/duck/ducky-script-usb-rubber-ducky-101).

The Pi will broadcast its own hidden (if so desired) Wifi network, so you'll be able to connect to it remotely, and interactively run
keyboard commands on the connected computer.

Basically, a remote penetration testing tool for $10, assuming you alreay have an SD card and a micro USB to USB A cable.


## DISCLAIMER

Use this tool at your own risk.

Please don't use it to do anything stupid or illegal. The purpose of the project is automation and learning. Not harming others.


## Installation and Setup

Start by going over [this great guide](https://randomnerdtutorials.com/raspberry-pi-zero-usb-keyboard-hid/) to turn your Pi into a software defined keyboard.

We only need to do steps 1-3. Here's a quick recap of the commands:

```bash
$ echo "dtoverlay=dwc2" | sudo tee -a /boot/firmware/config.txt
$ echo "dwc2" | sudo tee -a /etc/modules
$ sudo echo "libcomposite" | sudo tee -a /etc/modules
```

## Install the code

```bash
$ sudo apt-get install git python3-pip python3-venv
$ sudo mkdir -p /opt/ducky-server && sudo chown $USER:$USER /opt/ducky-server

$ git clone https://github.com/ozkatz/pi-remote-ducky.git /opt/ducky-server
$ cd /opt/ducky-server
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

Let's also create another directory to keep our custom Ducky scripts in:

```bash
$ sudo mkdir -p /opt/ducky-scripts && sudo chown $USER:$USER /opt/ducky-scripts
```

## Configure HID Service

Now that we have the code, let's configure the HID service to run on boot.

```bash
$ cd /opt/ducky-server
$ sudo cp kbsetup /usr/bin/kbsetup
$ sudo chmod +x /usr/bin/kbsetup
$ sudo cp ducky-hid.service /etc/systemd/system/
$ sudo systemctl daemon-reload
$ sudo systemctl enable ducky-hid.service
$ sudo systemctl start ducky-hid.service
```

Once done, there should be a file named `/dev/hidg0` in your system.

## Troubleshooting

If `/dev/hidg0` does not appear:

1.  **Check the service status:**
    ```bash
    sudo systemctl status ducky-hid
    ```
    Look for "Active: active (exited)" or any error messages.

2.  **Run kbsetup manually:**
    Stop the service and run the script manually to see any errors:
    ```bash
    sudo systemctl stop ducky-hid
    sudo /usr/bin/kbsetup
    ```
    *Note: If you see errors about "device or resource busy", it usually means the gadget is already active.*

3.  **Check Kernel Modules:**
    Ensure `libcomposite` is loaded:
    ```bash
    lsmod | grep libcomposite
    ```
    If not, check `/etc/modules` and try loading it manually: `sudo modprobe libcomposite`.

4.  **Check Kernel ConfigFS:**
    Ensure ConfigFS is mounted:
    ```bash
    mount | grep configfs
    ```
    It should show `configfs on /sys/kernel/config ...`.

5.  **Check boot config:**
    Verify `/boot/config.txt` contains `dtoverlay=dwc2`.



## Setup the server

```bash
$ cd /opt/ducky-server
$ sudo cp ducky-server.service /etc/systemd/system/
$ sudo systemctl daemon-reload
$ sudo systemctl enable ducky-server
$ sudo systemctl start ducky-server
```

## Connecting to the Pi

You have two options for connecting to your Pi:
1.  **Access Point Mode:** The Pi creates its own hidden Wi-Fi network.
2.  **Client Mode:** The Pi connects to your existing Wi-Fi network.

### Option 1: Access Point Mode (Standalone)

Basically, [follow this guide](https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md).
Here's a recap:

```bash
$ sudo apt-get install dnsmasq hostapd
$ sudo systemctl stop dnsmasq
$ sudo systemctl stop hostapd
```

Edit `/etc/dhcpcd.conf`, pasting in the following:

    interface wlan0
        static ip_address=192.168.4.1/24
        nohook wpa_supplicant

Edit `/etc/dnsmasq.conf`, pasting in the following:

    interface=wlan0      # Use the require wireless interface - usually wlan0
      dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h

And `/etc/hostapd/hostapd.conf`, with the following content:

    interface=wlan0
    driver=nl80211
    ssid=mywifinet
    hw_mode=g
    channel=7
    wmm_enabled=0
    macaddr_acl=0
    auth_algs=1
    ignore_broadcast_ssid=0
    wpa=2
    wpa_passphrase=evilraspberry
    wpa_key_mgmt=WPA-PSK
    wpa_pairwise=TKIP
    rsn_pairwise=CCMP

Feel free to rename the Wifi network to something else, and of course, change its password.

Lastly, edit `/etc/default/hostapd`:

    DAEMON_CONF="/etc/hostapd/hostapd.conf"

Finally, reboot your Pi (or simply connect it using the micro USB connection to the host computer).
Be sure to use the USB port labeled "USB" and not the one labeled "PWR". Wait a couple of minutes and try to connect to the new Wifi network we created.

Once connected, direct your browser at [http://192.168.4.1:5000/](http://192.168.4.1:5000/).

### Option 2: Client Mode (Connect to existing Wifi)

If you prefer the Pi to connect to your home/office Wi-Fi:

1.  **Do NOT** install `dnsmasq` or `hostapd`.
2.  **Do NOT** modify `/etc/dhcpcd.conf` with a static IP.
3.  Edit the Wi-Fi configuration:

    ```bash
    $ sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
    ```

    Add your network details to the bottom of the file (you can use the `wpa_supplicant.conf.sample` in this repo as a template):

    ```text
    network={
        ssid="YOUR_WIFI_SSID"
        psk="YOUR_WIFI_PASSWORD"
        key_mgmt=WPA-PSK
    }
    ```

4.  Reboot the Pi.

**Accessing the Server:**
Once the Pi is connected to your Wi-Fi, you can access it using its hostname. By default, this is `raspberrypi`.

*   Try: [http://raspberrypi.local:5000/](http://raspberrypi.local:5000/)
*   If you changed the hostname (via `sudo raspi-config`), use `http://<new-hostname>.local:5000/`.

*Note: This requires mDNS support (Avahi), which is standard on most devices. If it doesn't work, you'll need to find the Pi's IP address from your router.*
