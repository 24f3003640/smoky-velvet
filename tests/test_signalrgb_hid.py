import unittest
from unittest.mock import patch, MagicMock
from core.color import Color
from hardware.signalrgb_hid import SignalRGBRawHIDAdapter, CMD_SIGNALRGB_ENABLE, CMD_SIGNALRGB_DISABLE, CMD_SIGNALRGB_STREAM

class TestSignalRGBRawHID(unittest.TestCase):
    @patch('os.open')
    @patch('os.write')
    def test_connect_sends_enable(self, mock_write, mock_open):
        mock_open.return_value = 42
        adapter = SignalRGBRawHIDAdapter(device_path="/dev/hidraw1")

        success = adapter.connect()
        self.assertTrue(success)
        self.assertTrue(adapter.is_connected)

        # First write must be CMD_SIGNALRGB_ENABLE (0x25)
        mock_write.assert_called()
        first_call_bytes = mock_write.call_args_list[0][0][1]
        self.assertEqual(len(first_call_bytes), 32)
        self.assertEqual(first_call_bytes[0], CMD_SIGNALRGB_ENABLE)

    @patch('os.open')
    @patch('os.write')
    @patch('os.close')
    def test_disconnect_sends_disable_and_restores(self, mock_close, mock_write, mock_open):
        mock_open.return_value = 42
        adapter = SignalRGBRawHIDAdapter(device_path="/dev/hidraw1")
        adapter.connect()
        mock_write.reset_mock()

        adapter.disconnect()
        self.assertFalse(adapter.is_connected)

        # Disconnect writes CMD_SIGNALRGB_DISABLE (0x26)
        calls = [c[0][1] for c in mock_write.call_args_list]
        self.assertTrue(any(call[0] == CMD_SIGNALRGB_DISABLE for call in calls))
        mock_close.assert_called_with(42)

    @patch('os.open')
    @patch('os.write')
    def test_send_frame_chunking(self, mock_write, mock_open):
        mock_open.return_value = 42
        adapter = SignalRGBRawHIDAdapter(device_path="/dev/hidraw1")
        adapter.connect()
        mock_write.reset_mock()

        # Send 82-LED frame
        frame = [Color(130, 0, 160) for _ in range(82)]
        result = adapter.send_frame(frame, force=True)
        self.assertTrue(result)

        # 82 LEDs chunked into 9 LEDs max per packet = 10 packets (9*9=81 + 1)
        calls = mock_write.call_args_list
        self.assertEqual(len(calls), 10)

        for i, call in enumerate(calls):
            pkt = call[0][1]
            self.assertEqual(len(pkt), 32)
            self.assertEqual(pkt[0], CMD_SIGNALRGB_STREAM)
            start_idx = pkt[1]
            count = pkt[2]
            self.assertLessEqual(count, 9)
            if i < 9:
                self.assertEqual(count, 9)
                self.assertEqual(start_idx, i * 9)
            else:
                self.assertEqual(count, 1)
                self.assertEqual(start_idx, 81)

if __name__ == '__main__':
    unittest.main()
