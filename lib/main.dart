import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Gönüllü Pusula',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        scaffoldBackgroundColor: Colors.lightBlue[50],
      ),
      home: LoginScreen(),
    );
  }
}

// Giriş ekranı: JSON'dan kullanıcı verilerini yükleyip kontrol eder.
class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController tcController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  List<Map<String, String>> users = [];

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  // JSON dosyasından kullanıcı verilerini yükler.
  Future<void> _loadUsers() async {
    try {
      String data = await rootBundle.loadString('assets/kullanicilar.json');
      List<dynamic> jsonResult = json.decode(data);
      setState(() {
        users = jsonResult.map((e) {
          return {
            "İsim": e["İsim"] as String,
            "Soyisim": e["Soyisim"] as String,
            "TC": e["TC"] as String,
            "Şifre": e["Şifre"] as String,
          };
        }).toList();
        print("Yüklenen kullanıcı sayısı: ${users.length}");
      });
    } catch (e) {
      print("Kullanıcılar yüklenirken hata oluştu: $e");
      setState(() {
        users = [];
      });
    }
  }

  void _login() {
    String tc = tcController.text.trim();
    String password = passwordController.text.trim();

    var user = users.firstWhere(
          (user) => user["TC"] == tc && user["Şifre"] == password,
      orElse: () => {},
    );

    if (user.isNotEmpty) {
      List<Event> events = [];
      // Eğer özel TC'ler için farklı listeler tanımlamak isterseniz:
      if (tc == "12345678901") {
        events = sampleEventsMelek;
      } else if (tc == "98765432100") {
        events = sampleEventsAhmet;
      } else {
        // Diğer tüm kullanıcılar için varsayılan etkinlik listesi
        events = sampleEventsDefault;
      }
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => HomeScreen(
            userName: user["İsim"]!,
            userEvents: events,
          ),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Hatalı TC kimlik numarası veya şifre")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Giriş Yap"),
        backgroundColor: Colors.blue[700],
      ),
      body: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Yan yana iki görsel
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Flexible(
                  child: Image.network(
                    "https://drive.google.com/uc?export=view&id=1mQHWVSdvf6tJ6yhQw0sAmtTTTXa-7-Du",
                    height: 150,
                    width: 150,
                    fit: BoxFit.cover,
                  ),
                ),
                SizedBox(width: 10),
                Flexible(
                  child: Image.network(
                    "https://drive.google.com/uc?export=view&id=1hhM96UHTzykxIWcMykwhI-l3w3FDXdaa",
                    height: 150,
                    width: 150,
                    fit: BoxFit.cover,
                  ),
                ),
              ],
            ),
            SizedBox(height: 20),
            Text(
              "Gönüllü Pusula E-Devlet Giriş Ekranı",
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.blue[800],
              ),
            ),
            SizedBox(height: 20),
            TextField(
              controller: tcController,
              decoration: InputDecoration(labelText: "TC Kimlik No:"),
              keyboardType: TextInputType.number,
            ),
            TextField(
              controller: passwordController,
              decoration: InputDecoration(labelText: "Şifre:"),
              obscureText: true,
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _login,
              child: Text("Giriş Yap"),
            ),
          ],
        ),
      ),
    );
  }
}

// HomeScreen ekranı: Tasarımda değişiklik yapmadan etkinlik listesini gösterir.
class HomeScreen extends StatelessWidget {
  final String userName;
  final List<Event> userEvents;

  HomeScreen({required this.userName, required this.userEvents});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          "Gönüllü Pusula",
          style: TextStyle(color: Colors.white),
        ),
        backgroundColor: Colors.blue[700],
        actions: [
          IconButton(
            icon: Icon(Icons.exit_to_app),
            onPressed: () {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (context) => LoginScreen()),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.blue[200],
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(30),
                  bottomRight: Radius.circular(30),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Merhaba $userName, Hoşgeldin!",
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(height: 10),
                        Text(
                          "Bugün gönüllülük yolculuğunda senin için seçtiklerime göz at!",
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Image.network(
                    "https://drive.google.com/uc?export=view&id=1bCxzMgIVirzsFpM4FrssOY8_TEq93FYX",
                    width: 150,
                    height: 150,
                  ),
                ],
              ),
            ),
            SizedBox(height: 20),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                "Senin İçin Önerilen Etkinlikler",
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue[800],
                ),
              ),
            ),
            SizedBox(height: 10),
            ListView.builder(
              physics: NeverScrollableScrollPhysics(),
              shrinkWrap: true,
              itemCount: userEvents.length,
              itemBuilder: (context, index) {
                final event = userEvents[index];
                return Card(
                  margin: EdgeInsets.all(10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: ListTile(
                    leading: Image.network(
                      "https://drive.google.com/uc?export=view&id=10r6nW_uOTMN59OZk3Bg4BaaJcWRbsDJQ",
                      width: 50,
                      height: 50,
                      fit: BoxFit.cover,
                    ),
                    title: Text(event.title),
                    subtitle: Text("${event.city} • ${event.dateRange}"),
                    onTap: () {
                      showDialog(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: Text(event.title),
                          content: Text("${event.category} - ${event.location}"),
                          actions: [
                            TextButton(
                              child: Text("Kapat"),
                              onPressed: () => Navigator.pop(context),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

// Etkinlik modeli
class Event {
  final String city, title, category, dateRange, location;
  Event({
    required this.city,
    required this.title,
    required this.category,
    required this.dateRange,
    required this.location,
  });
}

// Özel etkinlik listeleri (varsa)
List<Event> sampleEventsMelek = [
  Event(city: "İstanbul", title: "Sokak Hayvanları İçin Mama Dağıtımı", category: "Çevre", dateRange: "15-16 Mart", location: "Kadıköy Meydanı"),
  Event(city: "Ankara", title: "Kitap Bağışı Kampanyası", category: "Eğitim", dateRange: "20 Mart", location: "Kızılay Meydanı"),
  Event(city: "İzmir", title: "Deniz Kıyısı Temizliği", category: "Çevre", dateRange: "22 Mart", location: "İnciraltı Sahili"),
  Event(city: "Bursa", title: "Huzurevi Ziyareti", category: "Sosyal Destek", dateRange: "25 Mart", location: "Bursa Yaşlı Bakım Evi"),
  Event(city: "Antalya", title: "Kan Bağışı Kampanyası", category: "Sağlık", dateRange: "30 Mart", location: "Antalya Kızılay Merkezi"),
  Event(city: "Eskişehir", title: "Engelli Çocuklar İçin Tiyatro Etkinliği", category: "Sanat", dateRange: "5 Nisan", location: "Eskişehir Kültür Merkezi"),
  Event(city: "Konya", title: "Yetim Çocuklarla Buluşma", category: "Sosyal Destek", dateRange: "10 Nisan", location: "Konya Çocuk Köyü"),
  Event(city: "Samsun", title: "Fidan Dikim Etkinliği", category: "Çevre", dateRange: "12 Nisan", location: "Samsun Orman Parkı"),
  Event(city: "Gaziantep", title: "Aşevi Gönüllülüğü", category: "Gıda Yardımı", dateRange: "18 Nisan", location: "Gaziantep Büyükşehir Belediyesi Aşevi"),
  Event(city: "Trabzon", title: "Deniz Temizleme Dalgıç Etkinliği", category: "Çevre", dateRange: "25 Nisan", location: "Trabzon Limanı"),
];

List<Event> sampleEventsAhmet = [
  Event(city: "Adana", title: "Kimsesiz Çocuklar İçin Oyun Günü", category: "Sosyal Destek", dateRange: "14 Mart", location: "Adana Çocuk Merkezi"),
  Event(city: "Mersin", title: "Sokak Sanatçılarıyla Buluşma", category: "Sanat", dateRange: "18 Mart", location: "Mersin Kültür Park"),
  Event(city: "Diyarbakır", title: "Tarihi Mekanları Tanıtma Gönüllülüğü", category: "Turizm", dateRange: "22 Mart", location: "Diyarbakır Sur İçi"),
  Event(city: "Hatay", title: "Depremzedeler İçin Yardım Toplama", category: "İnsani Yardım", dateRange: "28 Mart", location: "Hatay Gönüllü Merkezi"),
  Event(city: "Kayseri", title: "Lösemili Çocuklar İçin Moral Etkinliği", category: "Sağlık", dateRange: "3 Nisan", location: "Kayseri LÖSEV Merkezi"),
  Event(city: "Erzurum", title: "Üniversite Öğrencilerine Rehberlik", category: "Eğitim", dateRange: "7 Nisan", location: "Atatürk Üniversitesi Kampüsü"),
  Event(city: "Şanlıurfa", title: "Tarihi Yerlerin Dijital Arşivlenmesi", category: "Teknoloji", dateRange: "11 Nisan", location: "Göbeklitepe"),
  Event(city: "Malatya", title: "Köy Okullarına Kütüphane Kurma", category: "Eğitim", dateRange: "16 Nisan", location: "Malatya Akçadağ"),
  Event(city: "Van", title: "Doğa Yürüyüşü ve Çöp Toplama", category: "Çevre", dateRange: "22 Nisan", location: "Van Gölü Sahili"),
  Event(city: "Kocaeli", title: "Geri Dönüşüm Atölyesi", category: "Çevre", dateRange: "28 Nisan", location: "Kocaeli Bilim Merkezi"),
];

// Diğer tüm kullanıcılar için varsayılan etkinlik listesi
List<Event> sampleEventsDefault = [
  Event(city: "İstanbul", title: "Gönüllü Etkinliği", category: "Genel", dateRange: "1-2 Mayıs", location: "İstanbul Genel"),
  Event(city: "Ankara", title: "Topluluk Buluşması", category: "Genel", dateRange: "3-4 Mayıs", location: "Ankara Genel"),
  Event(city: "İzmir", title: "Sokak Temizliği", category: "Çevre", dateRange: "5 Mayıs", location: "İzmir Genel"),
];
