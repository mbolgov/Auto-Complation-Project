import reflex as rx

config = rx.Config(
    app_name="auto_completion_app",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)