import socket
import time

import cv2
import numpy as np
from PIL import Image
import argparse


class socket_connection():
    """
    Class for creating socket connection and retrieving images
    """
    def __init__(self, ip, port, camera, **kwargs):
        """
        Init of vars and creating socket connection object.
        Based on user input a different camera can be selected.
        1: Stereo camera 1280*360
        2: Stereo camera 2560*720
        3: Mono camera 320*240
        4: Mono camera 640*480
        """
        # Camera selection
        if camera == 1:
            self.size = 1382400  # RGB
            self.size = 921600  # YUV422
            self.width = 1280
            self.height = 360
            self.cam_id = 3
            self.res_id = 14
        elif camera == 2:
            self.size = 5529600  # RGB
            self.size = 3686400  # YUV422
            self.width = 2560
            self.height = 720
            self.cam_id = 3
            self.res_id = 13
        elif camera == 3:
            self.size = 230400 # RGB
            self.size = 153600 # YUV422
            self.width = 320
            self.height = 240
            self.cam_id = 0
            self.res_id = 1
        elif camera == 4:
            self.size = 921600 # RGB
            self.size = 614400 # YUV422
            self.width = 640
            self.height = 480
            self.cam_id = 0
            self.res_id = 2
        elif camera == 5:
            self.size = 2457600  # YUV422
            self.width = 1280
            self.height = 960
            self.cam_id = 0
            self.res_id = 3
        elif camera == 6:
            self.size = 9830400  # YUV422
            self.width = 1280
            self.height = 960
            self.cam_id = 0
            self.res_id = 3
        else:
            print(f"Invalid camera selected... choose between 1 and 4, got {camera}")
            exit(1)

        self.COLOR_ID = 13
        self.ip = ip
        self.port = port

        # Initialize socket socket connection
        self.s = socket.socket()
        try:
            self.s.connect((self.ip, self.port))
            print("Successfully connected with {}:{}".format(self.ip, self.port))
        except:
            print("ERR: Failed to connect with {}:{}".format(self.ip, self.port))
            exit(1)


    # def get_img(self):
    #     """
    #     Send signal to pepper to recieve image data, and convert to image data
    #     """
    #     self.s.send(b'getImg')
    #     pepper_img = b""
    #
    #     l = self.s.recv(self.size - len(pepper_img))
    #     while len(pepper_img) < self.size:
    #         pepper_img += l
    #         l = self.s.recv(self.size - len(pepper_img))
    #
    #     im = Image.frombytes("RGB", (self.width, self.height), pepper_img)
    #     cv_image = cv2.cvtColor(np.asarray(im, dtype=np.uint8), cv2.COLOR_BGRA2RGB)
    #
    #     return cv_image[:, :, ::-1]

    def get_img(self):
        #     """
        #     Send signal to pepper to recieve image data, and convert to image data
        #     """
        self.s.send(b'getImg')
        pepper_img = b""

        l = self.s.recv(self.size - len(pepper_img))
        while len(pepper_img) < self.size:
            pepper_img += l
            l = self.s.recv(self.size - len(pepper_img))

        arr = np.frombuffer(pepper_img, dtype=np.uint8)
        y = arr[0::2]
        u = arr[1::4]
        v = arr[3::4]
        yuv = np.ones((len(y)) * 3, dtype=np.uint8)
        yuv[::3] = y
        yuv[1::6] = u
        yuv[2::6] = v
        yuv[4::6] = u
        yuv[5::6] = v
        yuv = np.reshape(yuv, (self.height, self.width, 3))
        image = Image.fromarray(yuv, 'YCbCr').convert('RGB')
        image = np.array(image)
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        return image

    def close_connection(self):
        """
        Close socket connection after finishing
        """
        return self.s.close()

    def say(self, text):
        self.s.sendall(bytes(f"say {text}".encode()))

    def enable_tracking(self):
        self.s.sendall(bytes("track True".encode()))

    def disable_tracking(self):
        self.s.sendall(bytes("track False".encode()))

    def nod(self):
        self.s.sendall(bytes("nod".encode()))

    def adjust_head(self, pitch, yaw):
        self.s.sendall(bytes("head {:0.2f} {:0.2f}".format(pitch, yaw).encode()))

    def idle(self):
        self.s.sendall(bytes("idle".encode()))

    def look(self, x, y):
        self.s.sendall(bytes("look;{:0.5f};{:0.5f}".format(x, y).encode()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="10.15.3.25",
                        help="Robot IP address. Default 127.0.0.1")
    parser.add_argument("--port", type=int, default=12347,
                        help="Pepper port number. Default 9559.")
    parser.add_argument("--cam_id", type=int, default=4,
                        help="Camera id according to pepper docs. Use 3 for "
                             "stereo camera and 0. Default is 3.")
    args = parser.parse_args()
    connect = socket_connection(ip=args.ip, port=args.port, camera=args.cam_id)

    # connect.enable_tracking()

    # connect.say("Hey it's pepper")

    count = 0
    while True:
        start_fps = time.time()
        img = connect.get_img()

        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

        myFPS = 1.0 / (time.time() - start_fps)
        cv2.putText(img, 'FPS: {:.1f}'.format(myFPS), (10, 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 0), 1,
                    cv2.LINE_AA)
        cv2.imshow('pepper stream', img)
        cv2.imwrite("test_images/frame%d.jpg" % count, img)  # save frame as JPEG file
        cv2.waitKey(1)
        count+=1

        # connect.enable_tracking()
    # cv2.destroyAllWindows()

    # connect.close_connection()
