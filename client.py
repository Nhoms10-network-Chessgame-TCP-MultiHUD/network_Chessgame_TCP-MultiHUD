
import pygame
import socket
import threading
import queue
from data.classes.Board import Board 

HOST = '127.0.0.1'  
PORT = 65432        
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_color = None
my_turn = False

try:
    s.connect((HOST, PORT))
    print("Đã kết nối tới server {}:{}".format(HOST, PORT))
    
    s.settimeout(5.0) 
    color_data = s.recv(1024).decode()
    
    if color_data == 'white':
        my_color = 'white'
        my_turn = True 
    elif color_data == 'black':
        my_color = 'black'
        my_turn = False
    else:
        print("Không nhận được màu hợp lệ từ server.")
        exit()
    
    print("Bạn là phe: {}".format(my_color.capitalize()))
    s.settimeout(1.0) 

except Exception as e:
    print("Không thể kết nối hoặc nhận màu từ server: {}".format(e))
    exit()
# --------------------
move_queue = queue.Queue() 
running_event = threading.Event()
running_event.set()

def receiver_thread(s, q, event):
    while event.is_set():
        try:
            data = s.recv(1024)
            if not data:
                print("Server đã ngắt kết nối.")
                event.clear()
                break
            
            mx, my = map(int, data.decode().split(','))
            q.put((mx, my))
        except socket.timeout:
            continue
        except Exception as e:
            print("Lỗi nhận dữ liệu: {}".format(e))
            event.clear()
            break

threading.Thread(target=receiver_thread, args=(s, move_queue, running_event), daemon=True).start()
# --------------------

pygame.init()
WINDOW_SIZE = (500, 500)
screen = pygame.display.set_mode(WINDOW_SIZE)
# Caption sẽ hiển thị màu của người chơi
pygame.display.set_caption("Chess - Client ({})".format(my_color.capitalize()))

board = Board(WINDOW_SIZE[0], WINDOW_SIZE[1])

def draw(display):
	display.fill('white')
	board.draw(display)
	pygame.display.update()

# --------------------
while running_event.is_set():
    mx, my = pygame.mouse.get_pos()

    while not move_queue.empty():
        opponent_mx, opponent_my = move_queue.get()
        board.handle_click(opponent_mx, opponent_my)
        
        if board.turn == my_color:
            my_turn = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running_event.clear()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            
            if my_turn and event.button == 1:
                
                board.handle_click(mx, my)
                
                try:
                    s.sendall("{},{}".format(mx, my).encode())
                except Exception as e:
                    print("Lỗi gửi dữ liệu: {}".format(e))
                    running_event.clear()

                if board.turn != my_color:
                    my_turn = False

    if board.is_in_checkmate('black'):
        print('White wins!')
        running_event.clear()
    elif board.is_in_checkmate('white'):
        print('Black wins!')
        running_event.clear()

    draw(screen)

print("Đóng kết nối.")
s.close()
pygame.quit()
