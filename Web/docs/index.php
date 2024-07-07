<?php
require_once "../php/Parsedown.php";

function get_safe_param($param_name) {
    return isset($_GET[$param_name]) ? htmlspecialchars($_GET[$param_name]) : null;
}

$doc = get_safe_param("doc");
$id = get_safe_param("id");

if ($doc) {
    $folder_path = __DIR__ . "/src/$doc";
    $csv_file = "$folder_path/files.csv";

    if (file_exists($csv_file)) {
        $articles = array_map('str_getcsv', file($csv_file));
        $headers = array_shift($articles);

        // Создаем ассоциативный массив статей
        $articles_data = [];
        foreach ($articles as $article) {
            $article_assoc = array_combine($headers, $article);
            $articles_data[] = $article_assoc;
        }

        // Построим древовидный список
        function build_tree(array &$elements, $parent = "") {
            $branch = array();
            foreach ($elements as &$element) {
                if ($element['Заголовок последней зависимости'] == $parent) {
                    $children = build_tree($elements, $element['Заголовок статьи']);
                    if ($children) {
                        $element['children'] = $children;
                    }
                    $branch[] = $element;
                    unset($element);
                }
            }
            return $branch;
        }

        $tree = build_tree($articles_data);

        // Функция для отображения древовидного списка статей
        function display_tree($tree) {
            echo '<ul>';
            foreach ($tree as $node) {
                $link = $node['ID'] ? '<a href="?doc=' . htmlspecialchars($_GET['doc']) . '&id=' . $node['ID'] . '">' . $node['Заголовок статьи'] . '</a>' : $node['Заголовок статьи'];
                echo '<li>' . $link;
                if (!empty($node['children'])) {
                    display_tree($node['children']);
                }
                echo '</li>';
            }
            echo '</ul>';
        }

        // Если был передан параметр ID, отображаем соответствующую статью
        if ($id) {
            foreach ($articles_data as $article) {
                if ($article['ID'] == $id) {
                    $article_file = "$folder_path/" . $article['Заголовок файла'];
                    if (file_exists($article_file)) {
                        $article_content = file_get_contents($article_file);
                        $article = $article_content;
                    } else {
                        $article = "Статья не найдена.";
                    }
                    break;
                }
            }
        }
    } else {
        echo "Файл files.csv не найден.";
    }
} else {
    echo "Параметр doc не передан.";
}
?>
<html>
<head>
    <title>RuMate</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="../css/style.css" media="all">
	<link rel="stylesheet" href="../css/articles.css" media="all">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="Description" content="RuMate">
    <meta http-equiv="Content-language" content="ru-RU">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&family=Roboto&display=swap" rel="stylesheet">
</head>
<div class="wrapper">
    <div class="sideBar">
        <div class="menu">
            <a href="/"><img class="icon" src="/images/file-text.svg" alt="Документация"></a>
            <a href="/talks"><img class="icon" src="/images/chat-left-text.svg" alt="Ассистент"></a>
            <a href="/settings"><img class="icon" src="/images/gear.svg" alt="Настройки"></a>
        </div>
    </div>
    <div class="page p2">
	    <div class="listtree">
            <?php display_tree($tree); ?>
	    </div>
	    <div class="article">
    <?php
        $safeArticle = htmlspecialchars($article, ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $parsedown = new Parsedown();
        $articleHtml = $parsedown->text($safeArticle);
        echo $articleHtml;
    ?>
	    </div>
	    <button class="ask-assistant-btn">Спросить ассистента</button>
    </div>
</div>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const listtree = document.querySelector('.listtree');

        listtree.addEventListener('click', function(event) {
            if (event.target.tagName === 'A') {
                const parentLi = event.target.parentElement;
                if (parentLi.querySelector('ul')) {
                    parentLi.classList.toggle('open');
                    event.preventDefault();
                }
            }
        });

        // Add class "has-children" to LI elements with nested ULs
        const listItems = document.querySelectorAll('.listtree li');
        listItems.forEach(item => {
            if (item.querySelector('ul')) {
                item.classList.add('has-children');
            }
        });
    });

    document.addEventListener('DOMContentLoaded', function () {
        const article = document.querySelector('.article');
        const btn = document.querySelector('.ask-assistant-btn');

        article.addEventListener('mouseup', function () {
            const selectedText = window.getSelection().toString().trim();
            if (selectedText.length > 0) {
                const range = window.getSelection().getRangeAt(0);
                const rect = range.getBoundingClientRect();

                btn.style.top = `${rect.top + window.scrollY - btn.offsetHeight - 30}px`;
                btn.style.left = `${rect.left + window.scrollX}px`;
                btn.style.display = 'block';

                btn.onclick = function () {
                    window.location.href = `/talks?a=new&q=Объясни что такое "${selectedText}"`;
                };
            } else {
                btn.style.display = 'none';
            }
        });

        document.addEventListener('mousedown', function (event) {
            if (!btn.contains(event.target)) {
                btn.style.display = 'none';
            }
        });
    });
</script>
</html>
