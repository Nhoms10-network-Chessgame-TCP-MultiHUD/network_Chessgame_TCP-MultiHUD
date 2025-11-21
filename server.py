
import socket
import threading
import queue
from data.classes.Board import Board 

HOST = '127.0.0.1'  
PORT = 65432        

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(2)
print("Server đang lắng nghe tại {}:{}".format(HOST, PORT))
print("Đang chờ 2 người chơi kết nối...")

conn_white, addr_white = s.accept()
print("Người chơi Trắng đã kết nối từ {}".format(addr_white))
conn_white.sendall(b'white')

conn_black, addr_black = s.accept()
print("Người chơi Đen đã kết nối từ {}".format(addr_black))
conn_black.sendall(b'black') 

print("\nTrò chơi bắt đầu!")
# --------------------


white_queue = queue.Queue() 
black_queue = queue.Queue()
running_event = threading.Event()
running_event.set()

def receiver_thread(conn, q, event):
    while event.is_set():
        try:
            data = conn.recv(1024)
            if not data:
                print("Một client đã ngắt kết nối.")
                event.clear()
                break
            
            mx, my = map(int, data.decode().split(','))
            q.put((mx, my))
        except socket.timeout:
            continue
        except Exception as e:
            event.clear()
            break

conn_white.settimeout(1.0) 
conn_black.settimeout(1.0) 

threading.Thread(target=receiver_thread, args=(conn_white, white_queue, running_event), daemon=True).start()
threading.Thread(target=receiver_thread, args=(conn_black, black_queue, running_event), daemon=True).start()
# --------------------

game_board = Board(500, 500)
current_turn = 'white'

try:
    while running_event.is_set():
        try:
            if current_turn == 'white':
                mx, my = white_queue.get(timeout=1.0) 
                forward_conn = conn_black 
            else:
                mx, my = black_queue.get(timeout=1.0) 
                forward_conn = conn_white 
        except queue.Empty:
            continue 

        print("Nhận click từ {}: {},{}".format(current_turn, mx, my))

        game_board.handle_click(mx, my)

        move_data = "{},{}".format(mx, my).encode()
        forward_conn.sendall(move_data)

        if game_board.turn != current_turn:
            current_turn = game_board.turn
            print("Lượt đã đổi sang: {}".format(current_turn))

        if game_board.is_in_checkmate('black'):
            print('White wins!')
            running_event.clear()
        elif game_board.is_in_checkmate('white'):
            print('Black wins!')
            running_event.clear()

except Exception as e:
    print("Lỗi trong vòng lặp server chính: {}".format(e))
finally:
    print("Đóng kết nối server.")
    running_event.clear()
    conn_white.close()
    conn_black.close()
    s.close()