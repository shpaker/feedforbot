package main

import (
	"fmt"
	"net/url"

	bot "github.com/shpaker/feedforbot/feedforbot/core"
)

func main() {
	s := "https://www.debian.org/News/news"

	url, err := url.Parse(s)
	if err != nil {
		panic(err)
	}
	target := bot.FeedSource{
		Url: *url,
	}

	articles := target.GetUpdates()

	for _, article := range articles {
		fmt.Printf("Заголовок: %s\n", article.Title)
		fmt.Printf("Дата публикации: %s\n", article.PublishedAt)
		fmt.Printf("URL: %s\n", article.Url.String())
		fmt.Printf("Текст: %s\n", article.Text)
		fmt.Printf("ID: %s\n", article.Id)
		fmt.Printf("Получено: %s\n", article.ReceivedAt)
		if len(article.Images) > 0 {
			fmt.Println("Изображения:")
			for _, img := range article.Images {
				fmt.Printf("  - %s\n", img.String())
			}
		}
		if len(article.Authors) > 0 {
			fmt.Println("Авторы:")
			for _, author := range article.Authors {
				fmt.Printf("  - %s\n", author)
			}
		}
		if len(article.Categories) > 0 {
			fmt.Println("Категории:")
			for _, category := range article.Categories {
				fmt.Printf("  - %s\n", category)
			}
		}
		fmt.Println("-------------------")
	}
}
