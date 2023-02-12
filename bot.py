import aiogram.utils.markdown as fmt
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from style_transfer import simple_transfer, gan_transfer
from config import TOKEN, NUM_STEPS, IMAGE_SIZE, STYLE_COEF
from torchvision.utils import save_image

TOKEN = TOKEN
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
photo_buffer = {}


# user info
class InfoAboutUser:
    def __init__(self):
        self.settings = {
            "num_steps": NUM_STEPS,
            "imsize": IMAGE_SIZE,
            "style_coef": STYLE_COEF,
        }
        self.photos = []

    def set_default_settings(self):
        self.settings = {
            "num_steps": NUM_STEPS,
            "imsize": IMAGE_SIZE,
            "style_coef": STYLE_COEF,
        }


# start
start_kb = InlineKeyboardMarkup()
start_kb.add(
    InlineKeyboardButton("Перенос одного стиля (NST)", callback_data="1_st")
)
start_kb.add(
    InlineKeyboardButton("Стиль Моне (GAN)", callback_data="photo2monet")
)

# settings
settings1_kb = InlineKeyboardMarkup()
settings1_kb.add(InlineKeyboardButton("Стандартные", callback_data="default"))
settings1_kb.add(InlineKeyboardButton("Расширенные", callback_data="custom"))
settings1_kb.add(InlineKeyboardButton("Назад", callback_data="main_menu"))

# advanced settings
settings2_st_kb = InlineKeyboardMarkup()
settings2_st_kb.add(
    InlineKeyboardButton("Кол-во итераций", callback_data="num_steps")
)
settings2_st_kb.add(
    InlineKeyboardButton("Размер изображения", callback_data="imsize")
)
settings2_st_kb.add(
    InlineKeyboardButton("Коэффициент стиля", callback_data="style_coef")
)
settings2_st_kb.add(InlineKeyboardButton("Далее", callback_data="next"))
settings2_st_kb.add(InlineKeyboardButton("Назад", callback_data="1_st"))

settings2_gan_kb = InlineKeyboardMarkup()
settings2_gan_kb.add(
    InlineKeyboardButton("Размер картинки", callback_data="imsize")
)
settings2_gan_kb.add(InlineKeyboardButton("Далее", callback_data="next"))
settings2_gan_kb.add(
    InlineKeyboardButton("Назад", callback_data="photo2monet")
)

# steps number
num_steps_kb = InlineKeyboardMarkup()
num_steps_kb.add(InlineKeyboardButton("100", callback_data="num_steps_100"))
num_steps_kb.add(InlineKeyboardButton("300", callback_data="num_steps_300"))
num_steps_kb.add(InlineKeyboardButton("1000", callback_data="num_steps_1000"))
num_steps_kb.add(InlineKeyboardButton("2000", callback_data="num_steps_2000"))
num_steps_kb.add(InlineKeyboardButton("Назад", callback_data="custom"))

# image size
imsize_kb = InlineKeyboardMarkup()
imsize_kb.add(InlineKeyboardButton("64x64", callback_data="imsize_64"))
imsize_kb.add(InlineKeyboardButton("128x128", callback_data="imsize_128"))
imsize_kb.add(InlineKeyboardButton("256x256", callback_data="imsize_256"))
imsize_kb.add(InlineKeyboardButton("512x512", callback_data="imsize_512"))
imsize_kb.add(InlineKeyboardButton("Назад", callback_data="custom"))

# style coefficient
st_cf_kb = InlineKeyboardMarkup()
st_cf_kb.add(InlineKeyboardButton("0.001", callback_data="style_coef_0.001"))
st_cf_kb.add(InlineKeyboardButton("0.01", callback_data="style_coef_0.01"))
st_cf_kb.add(InlineKeyboardButton("0.1", callback_data="style_coef_0.1"))
st_cf_kb.add(InlineKeyboardButton("1", callback_data="style_coef_1"))
st_cf_kb.add(InlineKeyboardButton("10", callback_data="style_coef_10"))
st_cf_kb.add(InlineKeyboardButton("Назад", callback_data="custom"))

# return
cancel_kb = InlineKeyboardMarkup()
cancel_kb.add(InlineKeyboardButton("Отмена", callback_data="main_menu"))


# main menu
@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def main_menu(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Мои возможности:")
    await callback_query.message.edit_reply_markup(reply_markup=start_kb)


@dp.message_handler(commands=["start"])
async def send_welcome(message):
    await bot.send_message(
        message.chat.id,
        f"Здравствуйте, {message.from_user.first_name}!\n"
        + "\n"
        + "Я — Style Transfer Bot. "
        "Умею переносить стиль с картинки на картинку. " + "Мои возможности:",
        reply_markup=start_kb,
    )

    photo_buffer[message.chat.id] = InfoAboutUser()


@dp.message_handler(commands=["creator"])
async def creator(message):
    await bot.send_message(
        message.from_user.id,
        "По всем вопросам: @interpolat1on",
        reply_markup=start_kb,
    )


@dp.message_handler(commands=["help"])
async def send_help(message):
    await bot.send_message(
        message.from_user.id, "Мои возможности:", reply_markup=start_kb
    )


@dp.message_handler(content_types=["text"])
async def get_text(message):
    await bot.send_message(
        message.chat.id,
        "Я не понимаю. Мои возможности:",
        reply_markup=start_kb,
    )


# simple style transfer
@dp.callback_query_handler(lambda c: c.data == "1_st")
async def st_1_style(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text(
        "Выберите настройки для переноса стиля:"
    )
    await callback_query.message.edit_reply_markup(reply_markup=settings1_kb)

    if callback_query.from_user.id not in photo_buffer:
        photo_buffer[callback_query.from_user.id] = InfoAboutUser()

    photo_buffer[callback_query.from_user.id].st_type = 1


# photo to monet
@dp.callback_query_handler(lambda c: c.data == "photo2monet")
async def photo2monet(callback_query):
    await bot.answer_callback_query(callback_query.id)

    await callback_query.message.edit_text(
        "Изображение будет стилизовано под картины Клода Моне. "
        + "Выберите настройки для переноса стиля:"
    )
    await callback_query.message.edit_reply_markup(reply_markup=settings1_kb)

    if callback_query.from_user.id not in photo_buffer:
        photo_buffer[callback_query.from_user.id] = InfoAboutUser()

    photo_buffer[callback_query.from_user.id].st_type = "photo2monet"


# default settings
@dp.callback_query_handler(lambda c: c.data == "default")
async def default_settings(callback_query):
    await bot.answer_callback_query(callback_query.id)

    if photo_buffer[callback_query.from_user.id].st_type == 1:
        await callback_query.message.edit_text(
            "Пришлите изображение, стиль с которого нужно перенeсти. "
            + "Для лучшего качества изображение лучше загружать как документ.",
            reply_markup=cancel_kb,
        )
        photo_buffer[callback_query.from_user.id].need_photos = 2

    elif photo_buffer[callback_query.from_user.id].st_type == "photo2monet":
        await callback_query.message.edit_text(
            "Пришлите мне фотографию, и я добавлю на нее стиль Клода Моне. "
            + "Для лучшего качества изображение лучше загружать как документ.",
            reply_markup=cancel_kb,
        )

        photo_buffer[callback_query.from_user.id].need_photos = 1

    photo_buffer[callback_query.from_user.id].set_default_settings()


# advanced settings
@dp.callback_query_handler(lambda c: c.data == "custom")
async def custom_settings(callback_query):
    await bot.answer_callback_query(callback_query.id)

    if photo_buffer[callback_query.from_user.id].st_type == "photo2monet":
        await callback_query.message.edit_text(
            fmt.text(
                fmt.text(fmt.hunderline("Текущие настройки:"))
                + fmt.text(
                    "\nРазмер изображения: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                    + "x"
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                ),
                fmt.text(
                    "\n" + fmt.hbold("\nВыберите настройки для изменения:")
                ),
            ),
            parse_mode="HTML",
        )
        await callback_query.message.edit_reply_markup(
            reply_markup=settings2_gan_kb
        )
    else:
        await callback_query.message.edit_text(
            fmt.text(
                fmt.text(fmt.hunderline("Текущие настройки:"))
                + fmt.text(
                    "\nКоличество итераций: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "num_steps"
                        ]
                    )
                ),
                fmt.text(
                    "\nРазмер изображения: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                    + "x"
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                ),
                fmt.text(
                    "\nКоэффициент стиля: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "style_coef"
                        ]
                    )
                    + "\n"
                    + fmt.hbold("\nВыберите настройки для изменения:")
                ),
            ),
            parse_mode="HTML",
        )
        await callback_query.message.edit_reply_markup(
            reply_markup=settings2_st_kb
        )


# steps number
@dp.callback_query_handler(lambda c: c.data == "num_steps")
async def set_num_steps(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text(
        fmt.text(
            fmt.text(fmt.hunderline("Текущие настройки:"))
            + fmt.text(
                "\nКоличество итераций: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "num_steps"
                    ]
                )
            ),
            fmt.text(
                "\nРазмер изображения: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "imsize"
                    ]
                )
                + "x"
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "imsize"
                    ]
                )
            ),
            fmt.text(
                "\nКоэффициент стиля: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "style_coef"
                    ]
                )
                + "\n"
                + fmt.hbold("\nВыберите количество итераций:")
            ),
        ),
        parse_mode="HTML",
    )
    await callback_query.message.edit_reply_markup(reply_markup=num_steps_kb)


# changing steps number
@dp.callback_query_handler(lambda c: c.data[:10] == "num_steps_")
async def change_num_steps(callback_query):
    await bot.answer_callback_query(callback_query.id)
    photo_buffer[callback_query.from_user.id].settings["num_steps"] = int(
        callback_query.data[10:]
    )

    await callback_query.message.edit_text(
        fmt.text(
            fmt.text(fmt.hunderline("Текущие настройки:"))
            + fmt.text(
                "\nКоличество итераций: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "num_steps"
                    ]
                )
            ),
            fmt.text(
                "\nРазмер изображения: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "imsize"
                    ]
                )
                + "x"
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "imsize"
                    ]
                )
            ),
            fmt.text(
                "\nКоэффициент стиля: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "style_coef"
                    ]
                )
                + "\n"
                + fmt.hbold("\nВыберите настройки для изменения:")
            ),
        ),
        parse_mode="HTML",
    )
    await callback_query.message.edit_reply_markup(
        reply_markup=settings2_st_kb
    )


# style coefficient
@dp.callback_query_handler(lambda c: c.data == "style_coef")
async def set_style_coef(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text(
        fmt.text(
            fmt.text(fmt.hunderline("Текущие настройки:"))
            + fmt.text(
                "\nКоличество итераций: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "num_steps"
                    ]
                )
            ),
            fmt.text(
                "\nРазмер изображения: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "imsize"
                    ]
                )
                + "x"
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "imsize"
                    ]
                )
            ),
            fmt.text(
                "\nКоэффициент стиля: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "style_coef"
                    ]
                )
                + "\n"
                + fmt.hbold("\nВыберите коэффициент стиля:")
            ),
        ),
        parse_mode="HTML",
    )
    await callback_query.message.edit_reply_markup(reply_markup=st_cf_kb)


# changing style coefficient
@dp.callback_query_handler(lambda c: c.data[:11] == "style_coef_")
async def change_style_coef(callback_query):
    await bot.answer_callback_query(callback_query.id)
    photo_buffer[callback_query.from_user.id].settings["style_coef"] = float(
        callback_query.data[11:]
    )

    await callback_query.message.edit_text(
        fmt.text(
            fmt.text(fmt.hunderline("Текущие настройки:"))
            + fmt.text(
                "\nКоличество итераций: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "num_steps"
                    ]
                )
            ),
            fmt.text(
                "\nРазмер изображения: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "imsize"
                    ]
                )
                + "x"
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "imsize"
                    ]
                )
            ),
            fmt.text(
                "\nКоэффициент стиля: "
                + str(
                    photo_buffer[callback_query.from_user.id].settings[
                        "style_coef"
                    ]
                )
                + "\n"
                + fmt.hbold("\nВыберите настройки для изменения:")
            ),
        ),
        parse_mode="HTML",
    )
    await callback_query.message.edit_reply_markup(
        reply_markup=settings2_st_kb
    )


# image size
@dp.callback_query_handler(lambda c: c.data == "imsize")
async def set_image_size(callback_query):
    await bot.answer_callback_query(callback_query.id)

    if photo_buffer[callback_query.from_user.id].st_type == "photo2monet":
        await callback_query.message.edit_text(
            fmt.text(
                fmt.text(fmt.hunderline("Текущие настройки:"))
                + fmt.text(
                    "\nРазмер изображения: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                    + "x"
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                ),
                fmt.text("\n" + fmt.hbold("\nВыберите размер изображения:")),
            ),
            parse_mode="HTML",
        )
    else:
        await callback_query.message.edit_text(
            fmt.text(
                fmt.text(fmt.hunderline("Текущие настройки:"))
                + fmt.text(
                    "\nКоличество итераций: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "num_steps"
                        ]
                    )
                ),
                fmt.text(
                    "\nРазмер изображения: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                    + "x"
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                ),
                fmt.text(
                    "\nКоэффициент стиля: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "style_coef"
                        ]
                    )
                    + "\n"
                    + fmt.hbold("\nВыберите размер изображения:")
                ),
            ),
            parse_mode="HTML",
        )

    await callback_query.message.edit_reply_markup(reply_markup=imsize_kb)


# changing image size
@dp.callback_query_handler(lambda c: c.data[:7] == "imsize_")
async def change_imsize(callback_query):
    await bot.answer_callback_query(callback_query.id)
    photo_buffer[callback_query.from_user.id].settings["imsize"] = int(
        callback_query.data[7:]
    )

    if photo_buffer[callback_query.from_user.id].st_type == "photo2monet":
        await callback_query.message.edit_text(
            fmt.text(
                fmt.text(fmt.hunderline("Текущие настройки:"))
                + fmt.text(
                    "\nРазмер изображения: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                    + "x"
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                ),
                fmt.text(
                    "\n" + fmt.hbold("\nВыберите настройки для изменения:")
                ),
            ),
            parse_mode="HTML",
        )
        await callback_query.message.edit_reply_markup(
            reply_markup=settings2_gan_kb
        )

    else:
        await callback_query.message.edit_text(
            fmt.text(
                fmt.text(fmt.hunderline("Текущие настройки:"))
                + fmt.text(
                    "\nКоличество итераций: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "num_steps"
                        ]
                    )
                ),
                fmt.text(
                    "\nРазмер изображения: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                    + "x"
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "imsize"
                        ]
                    )
                ),
                fmt.text(
                    "\nКоэффициент стиля: "
                    + str(
                        photo_buffer[callback_query.from_user.id].settings[
                            "style_coef"
                        ]
                    )
                    + "\n"
                    + fmt.hbold("\nВыберите настройки для изменения:")
                ),
            ),
            parse_mode="HTML",
        )
        await callback_query.message.edit_reply_markup(
            reply_markup=settings2_st_kb
        )


# load images
@dp.callback_query_handler(lambda c: c.data == "next")
async def load_images(callback_query):
    if photo_buffer[callback_query.from_user.id].st_type == 1:
        await callback_query.message.edit_text(
            "Пришлите изображение, стиль с которого нужно перенeсти. "
            + "Для лучшего качества изображение лучше загружать как документ.",
            reply_markup=cancel_kb,
        )
        photo_buffer[callback_query.from_user.id].need_photos = 2

    elif photo_buffer[callback_query.from_user.id].st_type == "photo2monet":
        await callback_query.message.edit_text(
            "Пришлите мне фотографию, и я добавлю на нее стиль Клода Моне. "
            + "Для лучшего качества изображение лучше загружать как документ.",
            reply_markup=cancel_kb,
        )
        photo_buffer[callback_query.from_user.id].need_photos = 1


# getting image
@dp.message_handler(content_types=["photo", "document"])
async def get_image(message):
    if message.content_type == "photo":
        img = message.photo[-1]
    else:
        img = message.document
        if img.mime_type[:5] != "image":
            await bot.send_message(
                message.chat.id,
                "Загрузите, пожалуйста, файл в формате изображения.",
                reply_markup=start_kb,
            )
            return

    file_info = await bot.get_file(img.file_id)
    photo = await bot.download_file(file_info.file_path)

    if message.chat.id not in photo_buffer:
        await bot.send_message(
            message.chat.id,
            "Сначала выберите тип переноса стиля.",
            reply_markup=start_kb,
        )
        return

    if not hasattr(photo_buffer[message.chat.id], "need_photos"):
        await bot.send_message(
            message.chat.id,
            "Сначала выберите настройки переноса стиля.",
            reply_markup=settings1_kb,
        )
        return

    photo_buffer[message.chat.id].photos.append(photo)
    # print(photo_buffer[message.chat.id].photos)
    # single style transfer
    if photo_buffer[message.chat.id].st_type == 1:
        if photo_buffer[message.chat.id].need_photos == 2:
            photo_buffer[message.chat.id].need_photos = 1

            await bot.send_message(
                message.chat.id,
                "Пришлите изображение, на которое нужно перенести этот стиль. "
                + "Для лучшего качества изображение лучше загружать как документ.",
                reply_markup=cancel_kb,
            )

        elif photo_buffer[message.chat.id].need_photos == 1:
            await bot.send_message(message.chat.id, "Обработка...")

            output = await simple_transfer(
                photo_buffer[message.chat.id],
                *photo_buffer[message.chat.id].photos,
            )
            save_image(output, "./photos/generated.png")

            with open("./photos/generated.png", "rb") as file:
                await bot.send_document(
                    message.chat.id, file, caption="Готово!"
                )

            await bot.send_message(
                message.chat.id,
                "Что будем делать дальше?",
                reply_markup=start_kb,
            )

            del photo_buffer[message.chat.id]

    elif (
        photo_buffer[message.chat.id].st_type == "photo2monet"
        and photo_buffer[message.chat.id].need_photos == 1
    ):
        await bot.send_message(message.chat.id, "Начинаю обрабатывать...")

        output = await gan_transfer(
            photo_buffer[message.chat.id],
            *photo_buffer[message.chat.id].photos,
        )
        save_image(output, "./photos/generated.png")

        with open("./photos/generated.png", "rb") as file:
            await bot.send_document(message.chat.id, file, caption="Готово!")

        await bot.send_message(
            message.chat.id, "Что будем делать дальше?", reply_markup=start_kb
        )

        del photo_buffer[message.chat.id]


executor.start_polling(dp, skip_updates=True)
