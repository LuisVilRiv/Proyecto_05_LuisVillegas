import math
import random
from typing import Tuple, List, Optional

class CasinoTableRenderer:
    """Clase para renderizar elementos visuales de mesa de casino de forma realista"""
    
    @staticmethod
    def create_table_felt(canvas, width, height):
        """Crea un fondo de mesa de casino con tapete verde inmersivo y marco de madera"""
        # Borde de madera
        canvas.create_rectangle(0, 0, width, height, fill="#3e2723", outline="#1b0000", width=4)
        
        # Borde de cuero acolchado (Leather armrest)
        canvas.create_rectangle(15, 15, width-15, height-15, 
                               fill="#1a1a1a", outline="#000000", width=3)
        
        # Tapete verde central (Gradient simulado)
        colors = ["#0A3B22", "#0F5132", "#13623D", "#167248"]
        cx, cy = width / 2, height / 2
        for i in range(4):
            factor = 1.0 - (i * 0.15)
            w, h = (width-40)*factor, (height-40)*factor
            canvas.create_oval(cx-w/2, cy-h/2, cx+w/2, cy+h/2, fill=colors[i], outline="")
            
        # Tapete base por si el óvalo no cubre todo perfectamente
        canvas.create_rectangle(30, 30, width-30, height-30, 
                               fill="#0F5132", outline="#DAA520", width=3)

    @staticmethod
    def create_poker_chips(canvas, x, y, value, is_stacked=False):
        """Crea una ficha de poker visual premium. is_stacked dibuja sombra."""
        colors = {
            1: "#E0E0E0",  
            5: "#D32F2F",  
            10: "#1976D2", 
            25: "#388E3C", 
            100: "#212121", 
            500: "#7B1FA2"  
        }
        chip_color = colors.get(value, "#D32F2F")
        text_color = "#FFFFFF" if chip_color != "#E0E0E0" else "#000000"

        if is_stacked:
            # Sombra de pila
            for offset in range(3, 0, -1):
                canvas.create_oval(x-20, y-20+offset*2, x+20, y+20+offset*2, 
                                   fill="#111", outline="")

        # Borde base
        canvas.create_oval(x-20, y-20, x+20, y+20, fill=chip_color, outline="#333", width=1)
        
        # Marcas del borde (Edge spots)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sx, sy = x + 16 * math.cos(rad), y + 16 * math.sin(rad)
            canvas.create_oval(sx-3, sy-3, sx+3, sy+3, fill="#F5F5DC", outline="")

        # Círculo interior dorado
        canvas.create_oval(x-12, y-12, x+12, y+12, fill=chip_color, outline="#DAA520", width=2)
        
        # Valor
        canvas.create_text(x, y, text=str(value), fill=text_color, font=("Segoe UI", 9, "bold"))

    @staticmethod
    def create_card(canvas, x, y, rank, suit, face_up=True, back_image=None):
        """Crea una carta de juego visual con diseño moderno o textura fotográfica"""
        width, height = 60, 85
        r = 6 # Radio esquinas redondeadas
        
        if face_up:
            # Fondo carta
            canvas.create_polygon(
                x+r, y, x+width-r, y,
                x+width, y, x+width, y+r,
                x+width, y+height-r, x+width, y+height,
                x+width-r, y+height, x+r, y+height,
                x, y+height, x, y+height-r,
                x, y+r, x, y,
                fill="#FAFAFA", outline="#333", smooth=True, width=1
            )
            
            suit_symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
            suit_colors = {"H": "#D32F2F", "D": "#D32F2F", "C": "#212121", "S": "#212121"}
            symbol = suit_symbols.get(suit, "?")
            color = suit_colors.get(suit, "#212121")
            
            # Índices
            canvas.create_text(x+12, y+15, text=f"{rank}\n{symbol}", 
                              fill=color, font=("Arial", 11, "bold"), justify="center")
            
            # Centro gigante
            canvas.create_text(x+width/2, y+height/2 + 5, text=symbol, 
                              fill=color, font=("Arial", 36))
        else:
            if back_image:
                canvas.create_image(x + width/2, y + height/2, image=back_image)
                # Opcional: Borde para que se integre bien
                canvas.create_rectangle(x, y, x+width, y+height, outline="#333", width=1)
            else:
                # Dorso
                canvas.create_polygon(
                    x+r, y, x+width-r, y,
                    x+width, y, x+width, y+r,
                    x+width, y+height-r, x+width, y+height,
                    x+width-r, y+height, x+r, y+height,
                    x, y+height, x, y+height-r,
                    x, y+r, x, y,
                    fill="#1565C0", outline="#E0E0E0", smooth=True, width=2
                )
                # Patrón tartán simple
                for i in range(5, width-5, 8):
                    canvas.create_line(x+i, y+5, x+i, y+height-5, fill="#1976D2")
                for j in range(5, height-5, 8):
                    canvas.create_line(x+5, y+j, x+width-5, y+j, fill="#0D47A1")
                
                # Círculo central logo
                canvas.create_oval(x+15, y+25, x+45, y+55, fill="#FAFAFA", outline="#DAA520", width=2)
                canvas.create_text(x+30, y+40, text="♠", fill="#DAA520", font=("Arial", 20, "bold"))

    @staticmethod
    def create_slot_reel(canvas, x, y, symbols, blur=False):
        """Crea un carrete vertical de tragamonedas con 3 símbolos a gran escala."""
        width, height = 260, 410
        canvas.create_rectangle(x, y, x+width, y+height, fill="#ECEFF1", outline="#455A64", width=6)
        
        spacing = height // 3
        for i, symbol in enumerate(symbols):
            sx = x + width // 2
            sy = y + spacing * i + spacing // 2
            
            # Soporte de colores para emojis y letras
            colors = {"A": "#FBC02D", "K": "#78909C", "Q": "#8D6E63", 
                     "J": "#29B6F6", "7": "#E53935", "$": "#43A047", "*": "#AB47BC",
                     "🍒": "#C62828", "🍋": "#FBC02D", "🔔": "#FBC02D", "⭐": "#FBC02D", "💎": "#29B6F6", "7️⃣": "#C62828"}
            color = colors.get(symbol, "#333")
            
            if blur:
                # Efecto movimiento rápido vertical
                for offset in [-25, 0, 25]:
                    canvas.create_text(sx, sy + offset, text=symbol, 
                                      fill=color, font=("Impact", 64, "italic"), stipple="gray50")
            else:
                canvas.create_rectangle(sx-80, sy-50, sx+80, sy+50, fill="#FFF", outline="#CFD8DC", width=4)
                # Símbolo estático centrado en su fila
                canvas.create_text(sx, sy, text=symbol, fill=color, font=("Impact", 72))


    @staticmethod
    def create_roulette_wheel(canvas, cx, cy, radius, wheel_angle=0, ball_angle=None, image_manager=None):
        """Crea la rueda de ruleta, acepta rotación de rueda y rotación de bola"""
        
        # Intentar cargar textura fotorrealista primero
        wheel_img = None
        if image_manager:
            img_size = int(radius * 2.3) # Darle un poco de respiro al radio
            wheel_img = image_manager.get_rotated_image("texture_roulette_wheel", wheel_angle, (img_size, img_size))
            
        if wheel_img:
            # Dibujar la textura fotográfica
            canvas.create_image(cx, cy, image=wheel_img)
        else:
            # Base de madera exterior
            canvas.create_oval(cx-radius-15, cy-radius-15, cx+radius+15, cy+radius+15, 
                              fill="#3e2723", outline="#271410", width=4)
            canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, 
                              fill="#111", outline="#DAA520", width=3)
            
            # Secuencia Ruleta Europea
            seq = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 
                   10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
            n_pockets = 37
            arc_angle = 360 / n_pockets
            
            for i, num in enumerate(seq):
                start_deg = i * arc_angle + wheel_angle
                end_deg = start_deg + arc_angle
                
                if num == 0: color = "#2E7D32" # Verde
                elif num in {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}: color = "#C62828" # Rojo
                else: color = "#151515" # Negro
                
                # Dibujar "slice" (pie)
                canvas.create_arc(cx-radius, cy-radius, cx+radius, cy+radius,
                                  start=start_deg, extent=arc_angle+.5, 
                                  fill=color, outline="#E0A96D", width=1, style="pieslice")
                
                # Texto del número
                mid_angle = math.radians(start_deg + arc_angle/2)
                tx = cx + (radius * 0.75) * math.cos(mid_angle)
                ty = cy + (radius * 0.75) * math.sin(mid_angle)
                
                # Calcular orientación del texto para que apunte al centro (aproximadamente)
                canvas.create_text(tx, ty, text=str(num), fill="#FFFFFF", font=("Arial", 9, "bold"))
                
            # Cono central giratorio
            cr = radius * 0.5
            canvas.create_oval(cx-cr, cy-cr, cx+cr, cy+cr, fill="#E0A96D", outline="#8D6E63", width=2)
            # Patrón central para percibir rotación
            for a in range(0, 360, 45):
                rad = math.radians(a + wheel_angle)
                canvas.create_line(cx, cy, cx + cr*math.cos(rad), cy + cr*math.sin(rad), fill="#8D6E63", width=2)
                
            # Pomo central
            canvas.create_oval(cx-10, cy-10, cx+10, cy+10, fill="#FFD700", outline="#B8860B", width=2)

        # La bola siempre se dibuja encima

        if ball_angle is not None:
            bx = cx + (radius * 0.85) * math.cos(math.radians(ball_angle))
            by = cy + (radius * 0.85) * math.sin(math.radians(ball_angle))
            # Sombra de bola
            canvas.create_oval(bx-6+2, by-6+2, bx+6+2, by+6+2, fill="#000", outline="")
            # Bola blanca
            canvas.create_oval(bx-6, by-6, bx+6, by+6, fill="#FFFFFF", outline="#E0E0E0")

    @staticmethod
    def create_roulette_layout(canvas, x_offset, y_offset, w, h):
        """
        Dibuja un layout clásico de ruleta europea.
        Devuelve un diccionario con las coordenadas (rectángulos) para interacción.
        """
        regions = {} # { "0": (x1,y1,x2,y2), "1": ..., "red": ... }
        
        # Borde general
        canvas.create_rectangle(x_offset, y_offset, x_offset+w, y_offset+h, outline="#FFF", width=2)
        
        cell_w = w / 14  # 0 toma 1 col, 1-36 toma 12 cols, 2to1 toma 1 col
        cell_h = h / 5   # Main nums toma 3 filas, docenas algo, chnces algo.
        # Ajustaremos la grilla!
        
        # El 0 (verde)
        x0_start, y0_start = x_offset, y_offset
        x0_end, y0_end = x_offset + cell_w, y_offset + (cell_h * 3)
        canvas.create_rectangle(x0_start, y0_start, x0_end, y0_end, fill="#2E7D32", outline="#FFF", width=2)
        canvas.create_text((x0_start+x0_end)/2, (y0_start+y0_end)/2, text="0", fill="white", font=("Arial", 16, "bold"))
        regions["0"] = (x0_start, y0_start, x0_end, y0_end)
        
        # Números del 1 al 36 (en 3 filas y 12 columnas)
        reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        layout_num = [
            [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
            [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
            [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
        ]
        
        for row in range(3):
            for col in range(12):
                num = layout_num[row][col]
                x1 = x_offset + cell_w + (col * cell_w)
                y1 = y_offset + (row * cell_h)
                x2 = x1 + cell_w
                y2 = y1 + cell_h
                
                color = "#C62828" if num in reds else "#151515"
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#FFF", width=1)
                canvas.create_text((x1+x2)/2, (y1+y2)/2, text=str(num), fill="#FFF", font=("Arial", 14, "bold"))
                regions[str(num)] = (x1, y1, x2, y2)
                
        # Docenas (1st 12, 2nd 12, 3rd 12)
        doz_w = cell_w * 4
        for i, text in enumerate(["1st 12", "2nd 12", "3rd 12"]):
            x1 = x_offset + cell_w + (i * doz_w)
            y1 = y_offset + (cell_h * 3)
            x2 = x1 + doz_w
            y2 = y1 + cell_h
            canvas.create_rectangle(x1, y1, x2, y2, outline="#FFF", width=2)
            canvas.create_text((x1+x2)/2, (y1+y2)/2, text=text, fill="#FFF", font=("Arial", 12, "bold"))
            regions[str(i+1)] = (x1, y1, x2, y2) # Usamos clave "1", "2", "3" para docenas, cuidado que choca con números.
            # Mejor usar doc1, doc2, doc3
            regions[f"doc{i+1}"] = (x1, y1, x2, y2)

        # Suertes sencillas: 1-18, EVEN, RED, BLACK, ODD, 19-36
        bottom_cats = [
            ("1-18", "1-18", ""), ("EVEN", "par", ""), 
            ("RED", "rojo", "#C62828"), ("BLACK", "negro", "#151515"), 
            ("ODD", "impar", ""), ("19-36", "19-36", "")
        ]
        bot_w = (cell_w * 12) / 6
        for i, (label, key, bg) in enumerate(bottom_cats):
            x1 = x_offset + cell_w + (i * bot_w)
            y1 = y_offset + (cell_h * 4)
            x2 = x1 + bot_w
            y2 = y_offset + (cell_h * 5)
            # Rellenar con color si aplica (rojo/negro)
            if bg:
                canvas.create_rectangle(x1, y1, x2, y2, fill=bg, outline="#FFF", width=2)
            else:
                canvas.create_rectangle(x1, y1, x2, y2, outline="#FFF", width=2)
            canvas.create_text((x1+x2)/2, (y1+y2)/2, text=label, fill="#FFF", font=("Arial", 12, "bold"))
            regions[key] = (x1, y1, x2, y2)

        # Devolvemos el mapa de regiones para mapeo de clicks
        return regions

    @staticmethod
    def animate_chip_fall(canvas, start_x, start_y, end_x, end_y, steps=15):
        """Animación de ficha cayendo. Retorna secuencia de (x,y)."""
        positions = []
        for i in range(steps + 1):
            t = i / steps
            y = start_y + (end_y - start_y) * t + (math.sin(t * math.pi) * -40) # Parábola
            x = start_x + (end_x - start_x) * t
            positions.append((x, y))
        return positions

    @staticmethod
    def create_sparkle_effect(canvas, x, y, count=8):
        """Crea efecto de partículas brillantes"""
        sparkles = []
        for i in range(count):
            angle = (i * 360 / count) * math.pi / 180
            distance = random.randint(15, 60)
            sx = x + distance * math.cos(angle)
            sy = y + distance * math.sin(angle)
            size = random.randint(3, 8)
            
            sparkle = canvas.create_oval(sx-size, sy-size, sx+size, sy+size, 
                                       fill="#FBC02D", outline="#FFF2CC")
            sparkles.append(sparkle)
        return sparkles
