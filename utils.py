def turkce_format(datetime_obj):
    aylar = {
        "January": "Ocak", "February": "Şubat", "March": "Mart",
        "April": "Nisan", "May": "Mayıs", "June": "Haziran",
        "July": "Temmuz", "August": "Ağustos", "September": "Eylül",
        "October": "Ekim", "November": "Kasım", "December": "Aralık"
    }

    gunler = {
        "Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba",
        "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi",
        "Sunday": "Pazar"
    }

    gun = datetime_obj.strftime("%A")
    ay = datetime_obj.strftime("%B")
    tarih = datetime_obj.strftime(f"%d {aylar[ay]} %Y, {gunler[gun]} %H:%M")

    return tarih
