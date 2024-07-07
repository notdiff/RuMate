<?php
if (isset($_POST["url"])) {
	$apiUrl = 'https://api.example.com/endpoint';
	$data = array(
	    'key1' => 'value1',
	    'key2' => 'value2'
	);
	$jsonData = json_encode($data);
	$ch = curl_init($apiUrl);
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
	curl_setopt($ch, CURLOPT_POST, true);
	curl_setopt($ch, CURLOPT_POSTFIELDS, $jsonData);
	curl_setopt($ch, CURLOPT_HTTPHEADER, array(
	    'Content-Type: application/json',
	    'Content-Length: ' . strlen($jsonData)
	));
	$response = curl_exec($ch);
    $isSuccessChange = true;
}

if (isset($_POST["minutes"]) and is_numeric($_POST["minutes"])) {
    $cronJob = "*/${$_POST["minutes"]} * * * * /opt/api/venv/bin/python /opt/api/parse.py";
    //exec("crontab -l", $currentCronJobs);
    $currentCronJobs[] = $cronJob;
    //exec("echo \"" . implode("\n", $currentCronJobs) . "\" | crontab -");
	$isSuccessScheduling = true;
}
?>
<html>
<head>
    <title>RuMate</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="/css/style.css" media="all">
    <link rel="stylesheet" href="/css/users.css" media="all">
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
    <div class="page">
	    <div class="titleFlex">
		    <div class="title">Изменить настройки сервиса</div>
	    </div>
	    <div class="content">
		    <?php if ($isSuccessChange): ?>
			    <p>В течение 10 минут документация будет изменена на сайте и в моделях.</p>
		    <?php elseif ($isSuccessScheduling): ?>
			    <p>Была установлена задача парсить документацию.</p>
		    <?php endif; ?>
		    <form method="post" class="justify">
			    <input type="text" name="url" placeholder="URL документации https://wwww.rustore.ru/help/...">
			    <input type="submit" value="Изменить">
		    </form>
		    <form method="post" class="justify">
			    <input type="text" name="minutes" placeholder="Минут до перезагрузка парсинга">
			    <input type="submit" value="Изменить">
		    </form>
	    </div>
    </div>
</div>
</body>
</html>