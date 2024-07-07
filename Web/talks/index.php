<?php
require_once "../php/Parsedown.php";
session_start();
ini_set('session.gc_maxlifetime', 86400);
session_set_cookie_params(86400);
if (!isset($_SESSION['chats'])) {
    $_SESSION['chats'] = [];
}

function addChat($title, $messages) {
    $chat = [
        'id' => uniqid(),
        'created_at' => date('Y-m-d H:i:s'),
        'title' => $title,
        'messages' => []
    ];

    foreach ($messages as $message) {
        $chat['messages'][] = [
            'role' => $message['role'],
            'message' => $message['message'],
            'time' => date('Y-m-d H:i:s')
        ];
    }

    $_SESSION['chats'][] = $chat;
    return $chat['id'];
}
function addMessageToChat($chatId, $messages) {
    foreach ($_SESSION['chats'] as &$chat) {
        if ($chat['id'] == $chatId) {
            foreach ($messages as $message) {
                $chat['messages'][] = [
                    'role' => $message['role'],
                    'message' => $message['message'],
                    'time' => date('Y-m-d H:i:s')
                ];
            }
            break;
        }
    }
}

function displayChatTitles() {
    if (empty($_SESSION['chats'])) {
        echo '<div class="noTalks">Чатов пока что нет</div>';
    } else {
        foreach ($_SESSION['chats'] as $chat) {
            $class = "";
			if (isset($_GET["id"])) {
                if ($_GET["id"] == $chat["id"]) {
					 $class = ' class="here"';
                }
            }
            echo '<a href="?id=' . $chat['id'] . '"'.$class.'>' . htmlspecialchars($chat['title']) . '</a>';
        }
    }
}

function displayChatMessages($chatId) {
    foreach ($_SESSION['chats'] as $chat) {
        if ($chat['id'] == $chatId) {
            foreach ($chat['messages'] as $message) {
                if ($message['role'] == 'assistant') {
                    $safe = htmlspecialchars($message['message'], ENT_QUOTES | ENT_HTML5, 'UTF-8');
                    $parsedown = new Parsedown();
                    $msg = $parsedown->text($safe);
                    echo '<div class="message sAI">
                             <div class="avatar">
                                  AI
                             </div>
                             <div class="text">
                                  ' . $msg . '
                             </div>
                          </div>';
                } else if ($message['role'] == 'user') {
                    echo '<div class="message s1">
                             <div class="text">
                                  ' . htmlspecialchars($message['message']) . '
                             </div>
                          </div>';
                }
            }
            break;
        }
    }
}

if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_GET['a']) && $_GET['a'] == 'send') {
    $roles = $_POST['role'];
    $messages = $_POST['message'];
    $chatMessages = [];

    foreach ($roles as $index => $role) {
        $chatMessages[] = [
            'role' => $role,
            'message' => $messages[$index]
        ];
    }

    if (isset($_GET['id'])) {
        $chatId = $_GET['id'];
        if ($chatId == 'new') {
            // Заголовком является первое сообщение
            $title = $messages[0];
            $newChatId = addChat($title, $chatMessages);
            echo json_encode(['chat_id' => $newChatId]);
			exit();
        } else {
            // Добавляем сообщения в существующий чат
            addMessageToChat($chatId, $chatMessages);
            echo json_encode(['chat_id' => $chatId]);
            exit();
        }
    }
}

//// Пример добавления нового чата
//addChat('Тестовый чат', [
//    ['role' => 'user', 'message' => 'Привет!'],
//    ['role' => 'assistant', 'message' => 'Здравствуйте!']
//]);
//
//// Пример добавления сообщения в существующий чат
//if (!empty($_SESSION['chats'])) {
//    $chatId = $_SESSION['chats'][0]['id'];
//    addMessageToChat($chatId, 'user', 'Как дела?');
//}
?>
<html>
<head>
    <title>RuMate</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="/css/style.css" media="all">
	<link rel="stylesheet" href="/css/articles.css" media="all">
	<link rel="stylesheet" href="../css/dia.css" media="all">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="Description" content="RuMate">
    <meta http-equiv="Content-language" content="ru-RU">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&family=Roboto&display=swap" rel="stylesheet">
</head>
<body>
<div class="wrapper">
    <div class="sideBar">
        <div class="menu">
	        <a href="/"><img class="icon" src="/images/file-text.svg" alt="Документация"></a>
	        <a href="/talks"><img class="icon" src="/images/chat-left-text.svg" alt="Ассистент"></a>
	        <a href="/settings"><img class="icon" src="/images/gear.svg" alt="Настройки"></a>
        </div>
    </div>
    <div class="page p2">
	    <div class="chatstree">
		    <div class="titleFlex">
			    <div class="title">
				    Чаты
			    </div>
			    <a href="?a=new" class="new">
				    + Новый
			    </a>
		    </div>
            <?php displayChatTitles(); ?>
	    </div>
	    <?php if (isset($_GET["id"]) or $_GET["a"] == "new"): ?>
	    <div class="chat">
		    <div class="msglist" id="chat_messages">
                <?php if (isset($_GET["id"])) { displayChatMessages($_GET["id"]); } ?>
		    </div>
		    <div class="send">
			    <form id="form_chat" data-chatid="<?php echo $_GET['id'] ?? 'new'; ?>">
				    <textarea id="message_input" placeholder="Введите сообщение" required><?php echo $_GET['q'] ?? ''; ?></textarea><br>
				    <button type="submit">
					    <img src="/images/send.svg" alt="Отправить">
				    </button>
			    </form>
		    </div>
	    </div>
        <?php endif; ?>
    </div>
</div>
<script>
    document.getElementById('form_chat').addEventListener('submit', async function(event) {
        event.preventDefault();

        const form = event.target;
        const messageInput = document.getElementById('message_input');
        const chatTitleInput = document.getElementById('chat_title');
        const chatId = form.getAttribute('data-chatid');
        const messageText = messageInput.value;

        // Отобразить новое сообщение пользователя в чате
        const userMessage = document.createElement('div');
        userMessage.className = 'message s1';
        userMessage.innerHTML = `<div class="text">${messageText}</div>`;
        document.getElementById('chat_messages').appendChild(userMessage);

        // Заморозить поле ввода
        messageInput.disabled = true;

        // Отобразить сообщение от ассистента (загрузка)
        const assistantMessage = document.createElement('div');
        assistantMessage.className = 'message sAI mnew';
        assistantMessage.innerHTML = `<div class="avatar">AI</div><div class="text"><img class="loading" src="/images/svg.svg" alt="Loading..."></div>`;
        document.getElementById('chat_messages').appendChild(assistantMessage);

        // Отправить запрос в API
        const response = await fetch(`http://rumate.tw1.su:5000/searched_info?query=${encodeURIComponent(messageText)}`);
        const data = await response.json();
        const assistantReply = data.reply;

        // Обновить сообщение ассистента
        //assistantMessage.querySelector('.message').innerHTML = assistantReply;

        // Подготовить данные для POST-запроса
        const formData = new FormData();
        formData.append('role[]', 'user');
        formData.append('message[]', messageText);
        formData.append('role[]', 'assistant');
        formData.append('message[]', assistantReply);

        if (chatId === 'new' && chatTitleInput) {
            formData.append('title', chatTitleInput.value);
        }

        // Отправить POST-запрос на сервер
        const postResponse = await fetch(`?a=send&id=${chatId}`, {
            method: 'POST',
            body: formData
        });
        const postData = await postResponse.json();
        const newChatId = postData.chat_id;

        // Перенаправить пользователя на новый чат
        window.location.href = `?id=${newChatId}`;
    });

    document.getElementById('message_input').addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            document.getElementById('form_chat').dispatchEvent(new Event('submit', { 'bubbles': true }));
        }
    });
</script>
</body>
</html>