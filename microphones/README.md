# Microphone Documentation

This folder contains detailed technical specifications for each microphone used in the STT benchmark tests.

## Microphone Summary

| Microphone | Type | Pickup Pattern | Freq. Response | Price (USD) | Sample(s) |
|------------|------|----------------|----------------|-------------|-----------|
| [UGreen CM564](ugreen-cm564.md) | Desktop Gooseneck | Omnidirectional | 100-15,000 Hz | ~$25 | 1 |
| [Samson Q2U](samson-q2u.md) | Dynamic Desktop | Cardioid | 50-15,000 Hz | ~$70 | 2 |
| [Logitech H390](logitech-h390.md) | Wired Headset | Bi-directional | 100-10,000 Hz | ~$25 | 3 |
| [OnePlus Nord 3 5G](oneplus-nord-3-5g.md) | Smartphone | Omnidirectional | N/A | ~$450 | 4, 5 |
| [Audio-Technica ATR4697-USB](audio-technica-atr4697-usb.md) | Boundary | Omnidirectional | 50-15,000 Hz | ~$30 | 6, 7 |
| [Jabra Speak 510](jabra-speak-510.md) | Speakerphone | Omnidirectional | N/A | ~$120 | 8 |
| [Logitech C925e](logitech-c925e.md) | Webcam | Omnidirectional | N/A | ~$50 | 9 |
| [Maono Elf AU-UL10](maono-elf-au-ul10.md) | Lavalier | Omnidirectional | ~50-18,000 Hz | ~$25 | 10 |
| [Yealink BH72](yealink-bh72.md) | Wireless Headset | Directional (beamforming) | N/A | ~$175 | 11, 12 |
| [Audio-Technica ATR4750-USB](audio-technica-atr4750-usb.md) | Desktop Gooseneck | Omnidirectional | 50-13,000 Hz | ~$40 | 13 |

## Categories

### Desktop Microphones
- UGreen CM564 (Gooseneck)
- Samson Q2U (Dynamic)
- Audio-Technica ATR4697-USB (Boundary)
- Jabra Speak 510 (Speakerphone)
- Logitech C925e (Webcam)
- Audio-Technica ATR4750-USB (Gooseneck)

### Headsets
- Logitech H390 (Wired USB)
- Yealink BH72 (Wireless Bluetooth)

### Lavalier
- Maono Elf AU-UL10 (Wired USB)

### Mobile
- OnePlus Nord 3 5G (Smartphone)

## Pickup Pattern Distribution

| Pattern | Count | Microphones |
|---------|-------|-------------|
| Omnidirectional | 7 | UGreen CM564, OnePlus Nord 3, ATR4697, Jabra Speak 510, C925e, Maono Elf, ATR4750 |
| Cardioid | 1 | Samson Q2U |
| Bi-directional | 1 | Logitech H390 |
| Beamforming | 1 | Yealink BH72 |

## Price Range Distribution

| Range | Count | Microphones |
|-------|-------|-------------|
| Budget (<$30) | 4 | UGreen CM564, Logitech H390, Maono Elf, ATR4697 |
| Mid-range ($30-100) | 3 | Samson Q2U, Logitech C925e, ATR4750 |
| Premium (>$100) | 2 | Jabra Speak 510, Yealink BH72 |
| Device (phone) | 1 | OnePlus Nord 3 5G |

## Key Specifications for STT Analysis

When evaluating microphone suitability for speech-to-text:

1. **Pickup Pattern**: Cardioid/directional patterns reject background noise better
2. **Frequency Response**: Lower frequencies (50 Hz) capture fuller voice; upper range affects clarity of sibilants
3. **Sensitivity**: Higher sensitivity captures quieter sounds but may pick up more noise
4. **Noise Cancellation**: Hardware or software noise reduction can improve transcription accuracy
5. **Consistency**: Headsets and lavaliers maintain consistent mic-to-mouth distance
