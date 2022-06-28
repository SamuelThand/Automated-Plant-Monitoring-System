"""
Runs on boot
"""

import connections
import keys
import time

start_boot = time.time()

print('Booting system')

connections.wlan_connect(keys.wlan_ssid, keys.wlan_pw)

end_boot = time.time()

print('Time boot: ' + str(end_boot - start_boot))
