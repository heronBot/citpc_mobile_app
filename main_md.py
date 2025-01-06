from kivy.app import App
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import MDLabel
from kivy.uix.popup import Popup
import requests
import threading
import os
import time
import configparser
import threading

from android.permissions import request_permissions, Permission
from jnius import autoclass, cast


def request_permissions(self):
        # Request necessary permissions
        permissions = [Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION]
        def callback(permissions, grant_results):
            if all(grant_results):
               
                pass
            else:
                print("Some permissions were not granted.")
                Context = autoclass('android.content.Context')
                WifiManager = autoclass('android.net.wifi.WifiManager')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                WifiConfiguration = autoclass('android.net.wifi.WifiConfiguration')

                # Convert PythonActivity to Android Context
                context = cast(Context, PythonActivity.mActivity)

                # Get WifiManager service
                wifi_manager = context.getSystemService(Context.WIFI_SERVICE)
                
                # Start scan
                networks = wifi_manager.getConfiguredNetworks()
                ssids_to_connect = ["CITPC", "PC-ELEXCOMP", "CITAP"]
                for network in networks:

                    if network.SSID.replace('"', '') in ssids_to_connect:
                        wifi_config = WifiConfiguration()
                        wifi_config.SSID = f'"{network.SSID}"'
                        wifi_config.networkId = network.networkId
                        wifi_manager.disconnect()
                        wifi_manager.enableNetwork(network.networkId, True)
                        wifi_manager.reconnect()
                        self.button.text = f"Connected to {network.SSID.replace('\"', '')}"

        request_permissions(permissions, callback=callback)

class LoginScreen(BoxLayout):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.load_credentials()

    def load_credentials(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            self.ids.username.text = self.config.get('Login', 'username', fallback='')
            self.ids.password.text = self.config.get('Login', 'password', fallback='')

    def save_credentials(self, username, password):
        self.config['Login'] = {
            'username': username,
            'password': password
        }
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text

        print(username, password)

        # Show loading popup
        loading = LoadingPopup()
        loading.open()

        # Start a new thread for the login process
        threading.Thread(target=self.perform_login, args=(username, password, loading)).start()

    def perform_login(self, username, password, loading_popup):
        login_url = 'https://10.100.1.1:8090/login.xml'
        producttype = 'your_producttype'
        loginstate = ''
        timestamp = int(time.time() * 1000)

        payload = {
            'mode': '191',
            'username': username,
            'password': password,
            'a': timestamp,
            'producttype': producttype
        }

        if loginstate:
            payload['state'] = loginstate

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://10.100.1.1:8090/'
        }

        payload_encoded = '&'.join([f"{key}={requests.utils.quote(str(value))}" for key, value in payload.items()])

        try:
            response = requests.post(login_url, data=payload, headers=headers, verify=False, timeout=10)
            print(response.text)
            if response.status_code == 200:
                if 'You are signed in as' in response.text:
                    self.save_credentials(username, password)
                    self.ids.result_label.text = 'Login successful'
                    self.ids.result_label.color = 'green'
                else:
                    self.ids.result_label.text = f'Login failed: Invalid credentials'
                    self.ids.result_label.color = 'red'
            else:
                self.ids.result_label.text = f'Login failed: {response.status_code}'
                self.ids.result_label.color = 'red'
        except requests.exceptions.RequestException as e:
            self.ids.result_label.text = f'Login failed: {str(e)}'
        finally:
            loading_popup.dismiss()

class LoadingPopup(Popup):
    def __init__(self, **kwargs):
        super(LoadingPopup, self).__init__(**kwargs)
        self.size_hint = (.5, .5)
        self.auto_dismiss = False
        self.title = 'Loading...'
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        box.add_widget(MDLabel(text='Please wait...', size_hint_y=None, height=40))
        self.add_widget(box)

class CITPC_ConnectorApp(MDApp):
    def build(self):
        Window.size = [300, 600]
        return Builder.load_file('file.kv')

if __name__ == '__main__':
    threading.Thread(target=request_permissions).start()
    CITPC_ConnectorApp().run()
