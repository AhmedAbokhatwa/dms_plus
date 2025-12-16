# ========== الطريقة 1: Server Script (الأفضل) ==========
def before_render(doc, print_format):
    try:
        files = frappe.get_list("File",
            filters={"file_name": "company_gif.gif"},
            fields=["file_url"]
        )
        if files:
            doc.gif_url = files[0]["file_url"]
    except:
        doc.gif_url = "/files/company_gif.gif"

    return doc
