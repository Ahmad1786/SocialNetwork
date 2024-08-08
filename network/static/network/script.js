let main = document.querySelector('#main')

document.querySelector('#allposts').addEventListener('click', e => {
    e.preventDefault();
    requestAndUpdatePosts("all")
})

document.querySelector('#create-form').addEventListener('submit', (e) => {
    e.preventDefault()
    let contentInput = document.querySelector('#create-body')
    let content = contentInput.value

    fetch('/create-post', {
        method: 'POST',
        headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value},
        body: JSON.stringify({ content })
      })
      .then(response => response.json())
      .then(data => { 
          contentInput.value = ""
          requestAndUpdatePosts("profile", data["user_id"])
      })
      })

// the main page content that will be continuously replaced
// viewing profiles, liking, unliking, editing posts
main.addEventListener('click', e => {
    // handle certain clicks such as next, prev, and user links

    if (e.target.className === 'user-link') {
        let userId = e.target.dataset.user
        requestAndUpdatePosts('profile', userId)
    }

    else if (e.target.className === 'page-button') {
        let direction = e.target.id
        let curr = e.target.dataset.page
        let type = document.querySelector('.posts-label').id

        if (type.includes('profile')) {
            let userId = type.split('-')[1]
            goToAnotherPage(curr, direction, "profile", userId)
        }
        else {
            goToAnotherPage(curr, direction, type)
        }
    }

    else if (e.target.id === 'follow-button') {
        // POST to create follow - DELETE for delete
        fetch('update-following', {
            method: e.target.dataset.action,
            headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value},
            body: JSON.stringify({
                user: e.target.dataset.user
            })
          })
        .then(response => response.json())
        .then(data => {
              e.target.innerText = data['follow_string']
              document.querySelector('#followers').innerText = data['new_count']
              e.target.dataset.action = e.target.dataset.action === "POST" ? "DELETE" : "POST"
          })
    }

    else if (e.target.id == 'edit-post') {
        let postId = e.target.dataset.post
        let card = document.querySelector(`#content-${postId}`)
        let previousContent = card.innerText
        
        card.innerHTML = `
        <form method="post" id="edit-form">
          <textarea class="form-control">${previousContent}</textarea>
          <button type="submit">Save Changes</button>
        </form>
        `        
        document.querySelector('#edit-form').addEventListener('submit', (e) => {
            e.preventDefault()
            let newContent = e.target.querySelector('textarea').value

            fetch(`update-content/${postId}`, {
                method: 'PATCH',
                body: JSON.stringify({ newContent }),
                headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value},
            })
            .then(response => {
                if (response.status == 403) {
                    throw new Error("Can only Edit your own posts");
                }
                else if (response.status != 200) {
                    throw new Error("Some other error");
                }
                return response.json()
            })
            .then(data => {
                card.innerHTML = `<p class="card-text post-content" id="content-${postId}">${data['new_content']}</p>`
            })
            .catch(err => {
                document.querySelector('body').innerHTML = `<h1>${err}</h1>`
              });
        })
    
    }

    else if (e.target.className == 'like') {
        e.preventDefault()
        let postId = e.target.id.split('-')[1]
        fetch(`like-or-unlike/${postId}`, {
            method: 'PATCH',
            headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value},
        })
        .then(response => response.json())
        .then(data => {
           document.querySelector(`#numlikes-${postId}`).innerText = `Likes: ${data['new_count']}`
           e.target.innerText = e.target.innerText.trim() === 'Like' ? 'Unlike' : 'Like'
        }
        )
    }

})


// handle click on top user link seperately
document.querySelector('#top-user-item').addEventListener('click', e => {
    if ('STRONG-A'.includes(e.target.tagName)) {
        e.preventDefault();
    }
    let userId = document.querySelector('#top-user-item').dataset.user;
    requestAndUpdatePosts('profile', userId)
})

document.querySelector('#following').addEventListener('click', e => {
    e.preventDefault()
    requestAndUpdatePosts("following")
})


function requestAndUpdatePosts(type, userId=null) {
    // fetch get-posts
    // optionally provide userId for viewing a specific user
    // 3 types: all, following, profile
    let url = `posts/?type=${type}`
    if (userId !== null) {
        url += `&user=${userId}`
    }

    fetch(url)
    .then(response => response.text())
    .then(html => {
        main.innerHTML = html 
    })
}

function goToAnotherPage(currentPage, direction, type, userId=null) {
    url = `newpage/?curr=${currentPage}&direction=${direction}&type=${type}`
    if (userId !== null) {
        url += `&user=${userId}`
    }

    fetch(url)
    .then(response => response.text())
    .then(html => {
        main.innerHTML = html 
    })
}