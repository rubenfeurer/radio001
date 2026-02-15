## 1. Update Dockerfile Package Dependencies

- [x] 1.1 Remove hostapd from apt-get install list in backend/Dockerfile
- [x] 1.2 Replace dnsmasq with dnsmasq-base in apt-get install list
- [x] 1.3 Verify NetworkManager and wireless-tools packages remain in the list

## 2. Remove Obsolete Configuration File References

- [x] 2.1 Remove COPY config/hostapd/hostapd.conf.template line from backend/Dockerfile
- [x] 2.2 Remove COPY config/dnsmasq/dnsmasq.conf.template line from backend/Dockerfile
- [x] 2.3 Ensure boot-wifi-check.sh COPY statement remains intact

## 3. Verify and Test

- [x] 3.1 Build Docker image locally to verify no build errors
- [x] 3.2 Test that hotspot functionality still works via nmcli device wifi hotspot
- [x] 3.3 Confirm container starts and NetworkManager is operational
- [x] 3.4 Validate that CI build will succeed with updated Dockerfile