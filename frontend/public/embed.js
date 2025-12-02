(function() {
  // NeoBI Chat Widget Embed Script
  // NeoOne sitesine eklenecek script

  const NEOBI_URL = 'https://neobicb.neocortexbe.com';

  // Widget container oluştur
  const container = document.createElement('div');
  container.id = 'neobi-widget-container';
  container.innerHTML = `
    <div id="neobi-chat-button" style="
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      transition: transform 0.3s ease;
    ">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="white">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
      </svg>
    </div>
    <div id="neobi-chat-iframe-container" style="
      position: fixed;
      bottom: 90px;
      right: 20px;
      width: 380px;
      height: 550px;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      display: none;
      z-index: 9998;
    ">
      <iframe 
        id="neobi-chat-iframe"
        src="${NEOBI_URL}?embedded=true"
        style="width: 100%; height: 100%; border: none;"
        allow="microphone"
      ></iframe>
    </div>
  `;
  document.body.appendChild(container);

  // Chat button toggle
  const chatButton = document.getElementById('neobi-chat-button');
  const iframeContainer = document.getElementById('neobi-chat-iframe-container');
  const iframe = document.getElementById('neobi-chat-iframe');
  let isOpen = false;

  chatButton.addEventListener('click', function() {
    isOpen = !isOpen;
    iframeContainer.style.display = isOpen ? 'block' : 'none';
    chatButton.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';
  });

  // Token aktarımı için global fonksiyon
  // NeoOne frontend'i bu fonksiyonu çağırarak token gönderir
  window.NeoBIWidget = {
    // Token'ı widget'a gönder
    setToken: function(token) {
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage({
          type: 'NEOBI_SET_TOKEN',
          token: token
        }, NEOBI_URL);
      }
    },
    
    // Kullanıcı bilgisini gönder
    setUser: function(user) {
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage({
          type: 'NEOBI_SET_USER',
          user: user
        }, NEOBI_URL);
      }
    },

    // Widget'ı aç
    open: function() {
      isOpen = true;
      iframeContainer.style.display = 'block';
      chatButton.style.transform = 'rotate(90deg)';
    },

    // Widget'ı kapat
    close: function() {
      isOpen = false;
      iframeContainer.style.display = 'none';
      chatButton.style.transform = 'rotate(0deg)';
    }
  };

  // iframe yüklendiğinde token gönder (eğer varsa)
  iframe.addEventListener('load', function() {
    // NeoOne'dan token al ve gönder
    // Bu kısım NeoOne frontend'ine göre ayarlanacak
    const token = localStorage.getItem('neoone_token') || sessionStorage.getItem('token');
    if (token) {
      window.NeoBIWidget.setToken(token);
    }
  });

  console.log('NeoBI Widget loaded successfully');
})();
