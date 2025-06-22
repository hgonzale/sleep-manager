# Sleep Manager Homebridge Integration

Integrate your sleep-manager system with HomeKit using the `homebridge-http-switch` plugin.

## Quick Setup

1. **Install plugin**:
   ```bash
   npm install -g homebridge-http-switch
   ```

2. **Choose configuration**:
   - `config.json` - Single toggle switch with status monitoring
   - `config-separate-switches.json` - Separate wake/suspend switches

3. **Update configuration** in your Homebridge `config.json`:
   - Replace `192.168.1.100` with your waker machine's IP
   - Replace `your-waker-api-key-here` with your actual API key

4. **Restart Homebridge**

## API Endpoints Used

- **Wake**: `GET /waker/wake`
- **Suspend**: `GET /waker/suspend`
- **Status**: `GET /waker/status`

## Troubleshooting

**Test API manually**:
```bash
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/status
```

**Common issues**:
- Check waker machine connectivity
- Verify API key is correct
- Check Homebridge logs for errors

## Resources

- [homebridge-http-switch](https://github.com/Supereg/homebridge-http-switch)
- [sleep-manager Documentation](../README.md) 