import html
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()

SMTP_FROM_NAME = os.getenv(
    "SMTP_FROM_NAME",
    "Avoruna",
).strip()

SMTP_FROM_EMAIL = os.getenv(
    "SMTP_FROM_EMAIL",
    SMTP_USER,
).strip()


BRAND_GREEN = "#2F5D46"
BRAND_GREEN_DARK = "#244A38"
BACKGROUND_COLOR = "#F3F6F4"
TEXT_PRIMARY = "#17211C"
TEXT_SECONDARY = "#536159"
BORDER_COLOR = "#DCE5DF"


def build_otp_email_html(code: str) -> str:
    """
    Construye la plantilla HTML del correo de recuperación.

    La estructura utiliza tablas e inline CSS para mejorar la
    compatibilidad con Gmail, Outlook y clientes móviles.
    """

    safe_code = html.escape(str(code).strip())

    return f"""\
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <meta
        name="color-scheme"
        content="light"
    >
    <meta
        name="supported-color-schemes"
        content="light"
    >

    <title>Código de verificación de Avoruna</title>

    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: {BACKGROUND_COLOR};
            font-family: Arial, Helvetica, sans-serif;
        }}

        table {{
            border-spacing: 0;
        }}

        td {{
            padding: 0;
        }}

        img {{
            border: 0;
        }}

        .email-container {{
            width: 100%;
            max-width: 600px;
        }}

        .otp-code {{
            font-family: "Courier New", Courier, monospace;
            letter-spacing: 9px;
        }}

        @media only screen and (max-width: 600px) {{
            .email-wrapper {{
                padding: 20px 12px !important;
            }}

            .email-content {{
                padding: 28px 22px !important;
            }}

            .email-header {{
                padding: 26px 22px !important;
            }}

            .otp-code {{
                font-size: 30px !important;
                letter-spacing: 6px !important;
            }}
        }}
    </style>
</head>

<body>
    <!-- Texto previo visible en la bandeja de entrada -->
    <div
        style="
            display: none;
            max-height: 0;
            overflow: hidden;
            opacity: 0;
            color: transparent;
        "
    >
        Utiliza este código para recuperar el acceso a tu cuenta de Avoruna.
    </div>

    <table
        role="presentation"
        width="100%"
        cellpadding="0"
        cellspacing="0"
        border="0"
        style="
            width: 100%;
            background-color: {BACKGROUND_COLOR};
        "
    >
        <tr>
            <td
                align="center"
                class="email-wrapper"
                style="padding: 40px 16px;"
            >
                <table
                    role="presentation"
                    class="email-container"
                    width="600"
                    cellpadding="0"
                    cellspacing="0"
                    border="0"
                    style="
                        width: 100%;
                        max-width: 600px;
                        background-color: #FFFFFF;
                        border: 1px solid {BORDER_COLOR};
                        border-radius: 20px;
                        overflow: hidden;
                        box-shadow: 0 10px 30px rgba(28, 54, 42, 0.08);
                    "
                >
                    <!-- Encabezado -->
                    <tr>
                        <td
                            class="email-header"
                            style="
                                padding: 30px 36px;
                                background-color: {BRAND_GREEN};
                            "
                        >
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                            >
                                <tr>
                                    <td
                                        valign="middle"
                                        style="width: 54px;"
                                    >
                                        <div
                                            style="
                                                width: 46px;
                                                height: 46px;
                                                line-height: 46px;
                                                text-align: center;
                                                border-radius: 14px;
                                                background-color:
                                                    rgba(255, 255, 255, 0.14);
                                                color: #FFFFFF;
                                                font-size: 22px;
                                                font-weight: 700;
                                            "
                                        >
                                            A
                                        </div>
                                    </td>

                                    <td
                                        valign="middle"
                                        style="padding-left: 12px;"
                                    >
                                        <div
                                            style="
                                                margin: 0;
                                                color: #FFFFFF;
                                                font-size: 22px;
                                                line-height: 28px;
                                                font-weight: 700;
                                            "
                                        >
                                            Avoruna
                                        </div>

                                        <div
                                            style="
                                                margin-top: 4px;
                                                color:
                                                    rgba(255, 255, 255, 0.82);
                                                font-size: 12px;
                                                line-height: 18px;
                                            "
                                        >
                                            Tecnología inteligente para el
                                            cultivo de palta Hass
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Contenido principal -->
                    <tr>
                        <td
                            class="email-content"
                            style="padding: 36px;"
                        >
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                            >
                                <tr>
                                    <td>
                                        <div
                                            style="
                                                display: inline-block;
                                                padding: 7px 12px;
                                                border-radius: 999px;
                                                background-color: #EDF4F0;
                                                color: {BRAND_GREEN};
                                                font-size: 11px;
                                                line-height: 16px;
                                                font-weight: 700;
                                                text-transform: uppercase;
                                                letter-spacing: 0.5px;
                                            "
                                        >
                                            Verificación de identidad
                                        </div>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding-top: 20px;">
                                        <h1
                                            style="
                                                margin: 0;
                                                color: {TEXT_PRIMARY};
                                                font-size: 25px;
                                                line-height: 33px;
                                                font-weight: 700;
                                            "
                                        >
                                            Recupera el acceso a tu cuenta
                                        </h1>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding-top: 14px;">
                                        <p
                                            style="
                                                margin: 0;
                                                color: {TEXT_SECONDARY};
                                                font-size: 14px;
                                                line-height: 23px;
                                            "
                                        >
                                            Recibimos una solicitud para
                                            restablecer la contraseña de tu
                                            cuenta de Avoruna.
                                        </p>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding-top: 12px;">
                                        <p
                                            style="
                                                margin: 0;
                                                color: {TEXT_SECONDARY};
                                                font-size: 14px;
                                                line-height: 23px;
                                            "
                                        >
                                            Ingresa el siguiente código en la
                                            aplicación para continuar con la
                                            recuperación:
                                        </p>
                                    </td>
                                </tr>

                                <!-- Código OTP -->
                                <tr>
                                    <td
                                        align="center"
                                        style="padding: 28px 0 22px;"
                                    >
                                        <table
                                            role="presentation"
                                            cellpadding="0"
                                            cellspacing="0"
                                            border="0"
                                        >
                                            <tr>
                                                <td
                                                    align="center"
                                                    style="
                                                        padding:
                                                            20px 26px;
                                                        background-color:
                                                            #F1F6F3;
                                                        border:
                                                            1px solid #D7E5DC;
                                                        border-radius: 16px;
                                                    "
                                                >
                                                    <div
                                                        class="otp-code"
                                                        style="
                                                            color:
                                                                {BRAND_GREEN_DARK};
                                                            font-size: 36px;
                                                            line-height: 44px;
                                                            font-weight: 700;
                                                            white-space:
                                                                nowrap;
                                                        "
                                                    >
                                                        {safe_code}
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>

                                <!-- Tiempo de expiración -->
                                <tr>
                                    <td
                                        align="center"
                                        style="padding-bottom: 26px;"
                                    >
                                        <p
                                            style="
                                                margin: 0;
                                                color: {TEXT_SECONDARY};
                                                font-size: 12px;
                                                line-height: 19px;
                                            "
                                        >
                                            Este código vencerá en
                                            <strong
                                                style="
                                                    color: {TEXT_PRIMARY};
                                                "
                                            >
                                                10 minutos
                                            </strong>.
                                        </p>
                                    </td>
                                </tr>

                                <!-- Aviso de seguridad -->
                                <tr>
                                    <td
                                        style="
                                            padding: 16px 18px;
                                            background-color: #F8FAF9;
                                            border: 1px solid {BORDER_COLOR};
                                            border-radius: 14px;
                                        "
                                    >
                                        <table
                                            role="presentation"
                                            width="100%"
                                            cellpadding="0"
                                            cellspacing="0"
                                            border="0"
                                        >
                                            <tr>
                                                <td
                                                    valign="top"
                                                    style="
                                                        width: 28px;
                                                        color: {BRAND_GREEN};
                                                        font-size: 18px;
                                                        line-height: 22px;
                                                        font-weight: 700;
                                                    "
                                                >
                                                    !
                                                </td>

                                                <td
                                                    valign="top"
                                                    style="
                                                        color:
                                                            {TEXT_SECONDARY};
                                                        font-size: 12px;
                                                        line-height: 19px;
                                                    "
                                                >
                                                    Avoruna nunca te solicitará
                                                    este código por llamadas,
                                                    mensajes o redes sociales.
                                                    No lo compartas con otras
                                                    personas.
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding-top: 24px;">
                                        <p
                                            style="
                                                margin: 0;
                                                color: {TEXT_SECONDARY};
                                                font-size: 13px;
                                                line-height: 21px;
                                            "
                                        >
                                            Si no solicitaste este cambio,
                                            puedes ignorar este correo. Tu
                                            contraseña actual continuará
                                            funcionando con normalidad.
                                        </p>
                                    </td>
                                </tr>

                                <tr>
                                    <td
                                        style="
                                            padding-top: 28px;
                                            border-bottom:
                                                1px solid {BORDER_COLOR};
                                        "
                                    >
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding-top: 22px;">
                                        <p
                                            style="
                                                margin: 0;
                                                color: {TEXT_PRIMARY};
                                                font-size: 13px;
                                                line-height: 20px;
                                                font-weight: 700;
                                            "
                                        >
                                            Equipo de Avoruna
                                        </p>

                                        <p
                                            style="
                                                margin: 3px 0 0;
                                                color: {TEXT_SECONDARY};
                                                font-size: 12px;
                                                line-height: 18px;
                                            "
                                        >
                                            Plataforma inteligente para la
                                            evaluación de madurez de palta Hass
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Pie -->
                    <tr>
                        <td
                            align="center"
                            style="
                                padding: 20px 28px;
                                background-color: #F8FAF9;
                                border-top: 1px solid {BORDER_COLOR};
                            "
                        >
                            <p
                                style="
                                    margin: 0;
                                    color: #7A877F;
                                    font-size: 11px;
                                    line-height: 18px;
                                "
                            >
                                Este es un mensaje automático relacionado con
                                la seguridad de tu cuenta. No respondas a este
                                correo.
                            </p>

                            <p
                                style="
                                    margin: 6px 0 0;
                                    color: #8C9891;
                                    font-size: 10px;
                                    line-height: 16px;
                                "
                            >
                                © Avoruna · Ica, Perú
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def build_otp_email_text(code: str) -> str:
    """
    Versión de texto simple para clientes que no muestran HTML.
    """

    return (
        "AVORUNA\n"
        "Recuperación segura de cuenta\n\n"
        "Recibimos una solicitud para restablecer la contraseña "
        "de tu cuenta de Avoruna.\n\n"
        f"Tu código de verificación es: {code}\n\n"
        "Este código vence en 10 minutos.\n\n"
        "No compartas este código con otras personas. "
        "Avoruna nunca te lo solicitará por llamadas, mensajes "
        "o redes sociales.\n\n"
        "Si no solicitaste este cambio, puedes ignorar este correo. "
        "Tu contraseña actual continuará funcionando normalmente.\n\n"
        "Equipo de Avoruna\n"
        "Plataforma inteligente para la evaluación de madurez "
        "de palta Hass"
    )


def send_email_otp(to_email: str, code: str) -> None:
    """
    Envía el código OTP mediante correo electrónico.
    """

    if not all(
        [
            SMTP_HOST,
            SMTP_PORT,
            SMTP_USER,
            SMTP_PASS,
            SMTP_FROM_EMAIL,
        ]
    ):
        raise RuntimeError(
            "Faltan variables SMTP requeridas en el archivo .env."
        )

    destination = (to_email or "").strip()
    clean_code = str(code).strip()

    if not destination:
        raise ValueError(
            "El correo destinatario no puede estar vacío."
        )

    if not clean_code:
        raise ValueError(
            "El código de verificación no puede estar vacío."
        )

    message = MIMEMultipart("alternative")

    message["Subject"] = (
        f"{clean_code} es tu código de verificación de Avoruna"
    )
    message["From"] = (
        f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    )
    message["To"] = destination

    text_body = build_otp_email_text(clean_code)
    html_body = build_otp_email_html(clean_code)

    message.attach(
        MIMEText(
            text_body,
            "plain",
            "utf-8",
        )
    )

    message.attach(
        MIMEText(
            html_body,
            "html",
            "utf-8",
        )
    )

    try:
        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=20,
        ) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                SMTP_USER,
                SMTP_PASS,
            )

            server.sendmail(
                SMTP_FROM_EMAIL,
                [destination],
                message.as_string(),
            )

    except smtplib.SMTPAuthenticationError as ex:
        raise RuntimeError(
            "No se pudo autenticar con el servidor SMTP. "
            "Revisa SMTP_USER y SMTP_PASS."
        ) from ex

    except smtplib.SMTPException as ex:
        raise RuntimeError(
            "No se pudo enviar el correo de recuperación."
        ) from ex