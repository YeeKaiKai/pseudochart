import zmq
import time
import sys
import os
from datetime import datetime

# 設定輸出檔案路徑
if len(sys.argv) > 1:
    f_path = sys.argv[1]
else:
    # 使用時間戳記自動命名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "eye_tracking_data"
    os.makedirs(output_dir, exist_ok=True)
    f_path = os.path.join(output_dir, f"eyedata_{timestamp}.txt")

print(f"Eye tracking data will be saved to: {f_path}")

# 建立 ZMQ 連線
ctx = zmq.Context()
s = ctx.socket(zmq.SUB)
s.connect("tcp://127.0.0.1:5556")
s.setsockopt_string(zmq.SUBSCRIBE, 'TobiiStream')
s.setsockopt_string(zmq.SUBSCRIBE, 'TobiiState')

f = open(f_path, 'a')

try:
    while True:
        msg = s.recv()
        #print(msg)

        split_msg = msg.decode("utf-8").split()

        if split_msg[0] == 'TobiiStream':
            #timestamp = float(split_msg[1])
            timestamp1 = time.time()
            eyeX = float(split_msg[2])
            eyeY = float(split_msg[3])


            # Print the timestamp and gaze coordinates
            print(timestamp1, eyeX, eyeY)

            f.write(str(timestamp1) + ' ' + str(eyeX) + ' ' + str(eyeY) + '\n')

except KeyboardInterrupt:
    pass

f.close()
print("Done.")