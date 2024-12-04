import hashlib

import streamlit as st
import sqlite3
from streamlit_option_menu import option_menu
from PIL import Image
from io import BytesIO
import numpy as np
from keras.models import load_model

my_model = load_model('gs://goit_models/my_model_tf.keras')
# Створення або підключення до SQLite бази даних
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Створення таблиці, якщо вона не існує
c.execute('''
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT)
''')
conn.commit()

# Ініціалізація сесії
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ''

# Функції для хешування паролів
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Функції для перевірки паролів
def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# Функції для додавання користувачів
def add_userdata(username, password):
    c.execute('INSERT INTO users(username, password) VALUES (?, ?)', (username, password))
    conn.commit()

# Функції для входу
def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', (username, password))
    data = c.fetchall()
    return data

# Функції для виходу
def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''

# Навігація за допомогою option_menu
selected = option_menu(menu_title=None, options=["Home", "SignUp", "Login", "Profile", "Models"],
                       icons=["house", "person-plus", "log-in", "person", "gear"], menu_icon="cast", default_index=0,
                       orientation="horizontal")

if selected == "Home":
    st.title("Home Page")
    st.write("Welcome to the application!")

elif selected == "SignUp":
    st.title("Sign Up")
    new_user = st.text_input("Choose a username")
    new_password = st.text_input("Choose a password", type='password')
    if st.button("Sign Up"):
        add_userdata(new_user, make_hashes(new_password))
        st.success("You have successfully signed up!")

elif selected == "Login":
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        result = login_user(username, make_hashes(password))
        if check_hashes(password, result[0][1]):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome back, {username}!")
        else:
            st.error("Incorrect username or password.")

elif selected == "Profile":
    if st.session_state.logged_in:
        st.title("Your Profile")
        st.write(f"Username: {st.session_state.username}")
        if st.button("Logout"):
            logout()
    else:
        st.error("You are not logged in. Please login to see this page.")


elif selected == "Models":
    if st.session_state.logged_in:
        st.title("My models")
        model_type = st.sidebar.radio('Виберіть модель:', ['Моя згорткова нейромережа', 'VGG16'])
        # Заголовок сторінки
        st.title("Завантажте файт")
        
        uploaded_file = st.file_uploader("Виберіть файл...", type=["png","jpeg", ])

        if uploaded_file is not None:
            try:
                # Открываем загруженный файл
                img = Image.open(uploaded_file)

                grayscale_img = img.convert("L")

                resized_img = grayscale_img.resize((28, 28))

                # Сохраняем измененное изображение в буфер
                buffer = BytesIO()
                resized_img.save(buffer, format="PNG")
                buffer.seek(0)

                # Показываем измененное изображение
                st.image(resized_img, caption="Picture in 28x28", use_container_width=False)

            except Exception as e:
                st.error(f"Помилка обробки зображення: {e}")

        run_button = st.button("Run")
        class_names = ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat", "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]
        if run_button:
            img_array = np.array(resized_img)
            image_to_model = img_array.reshape((1, 28, 28, 1)).astype('float32') / 255
            if model_type == "Моя згорткова нейромережа":
                predictions = my_model.predict(image_to_model)
                
                predicted_probs = zip(class_names, predictions[0])
                # Выводим вероятности для каждого класса
                st.write("Всі ймовірності з класами:")
                for class_name, prob in predicted_probs:
                    st.write(f"{class_name}: {prob:.4f}")

                predicted_label = np.argmax(predictions, axis=1)[0]
                st.write(f'передбачення: {class_names[predicted_label]}')     
            elif model_type == "VGG16":
                st.write("Вы выбрали Опцию 2")


                
    else:
        st.error("You are not logged in. Please login to see this page.")

