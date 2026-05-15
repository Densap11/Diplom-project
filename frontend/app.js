const apiHost = window.location.hostname || "localhost";
const apiProtocol = window.location.protocol === "https:" ? "https:" : "http:";
const API_ROOT = `${apiProtocol}//${apiHost}:8000`;
const API_BASE = `${API_ROOT}/api/v1`;

const state = {
  token: localStorage.getItem("activity_token") || "",
  currentUser: null,
  categories: [],
  events: [],
  registrations: [],
  myEvents: [],
  manageableEvents: [],
  users: [],
  participants: [],
  view: "home",
  editingEventId: null,
};

const elements = {
  toast: document.getElementById("toast"),
  eventsGrid: document.getElementById("events-grid"),
  searchInput: document.getElementById("search-input"),
  categoryFilter: document.getElementById("category-filter"),
  eventCategory: document.getElementById("event-category"),
  userPill: document.getElementById("user-pill"),
  logoutButton: document.getElementById("logout-button"),
  guestBanner: document.getElementById("guest-banner"),
  myRegistrations: document.getElementById("my-registrations"),
  myEvents: document.getElementById("my-events"),
  adminUsers: document.getElementById("admin-users"),
  adminEvents: document.getElementById("admin-events"),
  adminUserSearch: document.getElementById("admin-user-search"),
  adminRoleFilter: document.getElementById("admin-role-filter"),
  participantsPanel: document.getElementById("participants-panel"),
  participantsTitle: document.getElementById("participants-title"),
  participantsList: document.getElementById("participants-list"),
  participantsClose: document.getElementById("participants-close"),
  template: document.getElementById("event-card-template"),
  limitField: document.getElementById("limit-field"),
  eventForm: document.getElementById("event-form"),
  eventFormTitle: document.getElementById("event-form-title"),
  cancelEditButton: document.getElementById("cancel-edit-button"),
  profileTitle: document.getElementById("profile-title"),
  profileNav: document.getElementById("profile-nav"),
  createNav: document.getElementById("create-nav"),
  adminNav: document.getElementById("admin-nav"),
  loginNav: document.getElementById("login-nav"),
  registerNav: document.getElementById("register-nav"),
  adminPanel: document.getElementById("admin-panel"),
  screens: document.querySelectorAll("[data-screen]"),
  navLinks: document.querySelectorAll("[data-view]"),
};

function showToast(message, isError = false) {
  elements.toast.textContent = message;
  elements.toast.classList.remove("hidden");
  elements.toast.style.background = isError ? "#a33030" : "#16365b";
  clearTimeout(showToast.timeoutId);
  showToast.timeoutId = setTimeout(() => elements.toast.classList.add("hidden"), 3200);
}

async function runWithButtonState(button, loadingText, action) {
  const previousText = button.textContent;
  button.disabled = true;
  button.classList.add("button--loading");
  button.textContent = loadingText;

  try {
    await action();
  } finally {
    button.disabled = false;
    button.classList.remove("button--loading");
    button.textContent = previousText;
  }
}

async function apiFetch(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {}),
  };

  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw new Error(data?.detail || "Произошла ошибка запроса");
  }

  return data;
}

function roleLabel(role) {
  return {
    student: "Студент",
    organizer: "Организатор",
    admin: "Администратор",
  }[role] || role;
}

function statusLabel(status) {
  return {
    draft: "Черновик",
    published: "Опубликовано",
    archived: "Архив",
    confirmed: "Подтверждено",
    cancelled: "Отменено",
    waiting_list: "Лист ожидания",
  }[status] || status;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function formatDate(dateString) {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(dateString));
}

function getCategoryName(categoryId) {
  const category = state.categories.find((item) => item.id === categoryId);
  return category ? category.name : `Категория #${categoryId}`;
}

function getEventTitle(eventId) {
  const event = [...state.events, ...state.myEvents, ...state.manageableEvents].find((item) => item.id === eventId);
  return event ? event.title : `Событие #${eventId}`;
}

function getConfirmedRegistration(eventId) {
  return state.registrations.find(
    (item) => item.event_id === eventId && item.status === "confirmed"
  );
}

function setView(view) {
  const user = state.currentUser;
  const isOrganizer = user && (user.role === "organizer" || user.role === "admin");
  const isAdmin = user && user.role === "admin";

  if ((view === "profile" || view === "create" || view === "admin") && !user) {
    state.view = "login";
  } else if (view === "create" && !isOrganizer) {
    state.view = "home";
  } else if (view === "admin" && !isAdmin) {
    state.view = "home";
  } else {
    state.view = view;
  }

  elements.screens.forEach((screen) => {
    screen.classList.toggle("screen--active", screen.dataset.screen === state.view);
  });

  elements.navLinks.forEach((link) => {
    link.classList.toggle("is-active", link.dataset.view === state.view);
  });
}

function applyHeaderState() {
  const user = state.currentUser;
  const isOrganizer = user && (user.role === "organizer" || user.role === "admin");
  const isAdmin = user && user.role === "admin";

  elements.userPill.classList.toggle("hidden", !user);
  elements.logoutButton.classList.toggle("hidden", !user);
  elements.profileNav.classList.toggle("hidden", !user);
  elements.createNav.classList.toggle("hidden", !isOrganizer);
  elements.adminNav.classList.toggle("hidden", !isAdmin);
  elements.loginNav.classList.toggle("hidden", !!user);
  elements.registerNav.classList.toggle("hidden", !!user);
  elements.guestBanner.classList.toggle("hidden", !!user);
  elements.adminPanel.classList.toggle("hidden", !isAdmin);

  if (user) {
    elements.userPill.textContent = "Профиль";
    elements.userPill.title = `${user.full_name} • ${roleLabel(user.role)}`;
    elements.profileTitle.textContent = user.full_name;
  } else {
    elements.userPill.removeAttribute("title");
    elements.profileTitle.textContent = "Личный кабинет";
  }
}

function populateCategories() {
  elements.categoryFilter.innerHTML = ['<option value="">Все категории</option>']
    .concat(
      state.categories.map((category) => (
        `<option value="${category.id}">${escapeHtml(category.name)}</option>`
      ))
    )
    .join("");

  elements.eventCategory.innerHTML = state.categories.length
    ? state.categories.map((category) => (
        `<option value="${category.id}">${escapeHtml(category.name)}</option>`
      )).join("")
    : '<option value="">Сначала создайте категорию</option>';

}

function renderEvents() {
  const searchValue = elements.searchInput.value.trim().toLowerCase();
  const categoryValue = elements.categoryFilter.value;
  const user = state.currentUser;
  const canRegister = user && (user.role === "student" || user.role === "admin");

  const filteredEvents = state.events.filter((event) => {
    const matchesSearch = event.title.toLowerCase().includes(searchValue);
    const matchesCategory = !categoryValue || String(event.category_id) === categoryValue;
    return matchesSearch && matchesCategory;
  });

  elements.eventsGrid.innerHTML = "";

  if (!filteredEvents.length) {
    elements.eventsGrid.innerHTML = '<div class="empty-state">По текущим фильтрам событий не найдено.</div>';
    return;
  }

  filteredEvents.forEach((event) => {
    const card = elements.template.content.firstElementChild.cloneNode(true);
    const cover = card.querySelector(".event-card__cover");
    const registerButton = card.querySelector(".event-register");
    const cancelButton = card.querySelector(".event-cancel");
    const capacityValue = card.querySelector(".event-card__capacity");
    const registration = getConfirmedRegistration(event.id);
    const isRegistered = Boolean(registration);
    const remainingPlaces = event.remaining_places;
    const isFull = !event.is_unlimited && remainingPlaces === 0;

    card.querySelector(".event-card__category").textContent = getCategoryName(event.category_id);
    card.querySelector(".event-card__status").textContent = statusLabel(event.status);
    card.querySelector(".event-card__title").textContent = event.title;
    card.querySelector(".event-card__summary").textContent = event.short_description;
    card.querySelector(".event-card__date").textContent = formatDate(event.event_date);
    card.querySelector(".event-card__location").textContent = event.location;
    card.querySelector(".event-card__contacts").textContent = event.contacts;
    capacityValue.textContent = event.is_unlimited
      ? "Без ограничения"
      : `${remainingPlaces} из ${event.max_participants} мест осталось`;

    if (event.image_url) {
      cover.src = `${API_ROOT}${event.image_url}`;
      cover.classList.remove("hidden");
    }

    registerButton.addEventListener("click", () => registerForEvent(event.id));
    cancelButton.addEventListener("click", () => cancelRegistration(event.id));

    if (!user) {
      registerButton.textContent = "Войти для записи";
      cancelButton.classList.add("hidden");
    } else if (!canRegister) {
      registerButton.textContent = "Запись доступна студентам";
      registerButton.disabled = true;
      cancelButton.classList.add("hidden");
    } else if (isRegistered) {
      registerButton.textContent = "Вы записаны";
      registerButton.classList.remove("button--primary");
      registerButton.classList.add("button--success");
      cancelButton.classList.remove("hidden");
    } else if (isFull) {
      registerButton.textContent = "Мест нет";
      registerButton.disabled = true;
      cancelButton.classList.add("hidden");
      capacityValue.classList.add("event-card__capacity--full");
    } else {
      cancelButton.classList.add("hidden");
    }

    elements.eventsGrid.appendChild(card);
  });
}

function renderProfile() {
  elements.myRegistrations.innerHTML = state.registrations.length
    ? state.registrations
        .map(
          (item) => `
            <div class="list-item">
              <strong>${escapeHtml(getEventTitle(item.event_id))}</strong><br />
              Статус: ${escapeHtml(statusLabel(item.status))}<br />
              Дата записи: ${formatDate(item.created_at)}
            </div>
          `
        )
        .join("")
    : '<div class="empty-state">Вы пока не записались ни на одно событие.</div>';

  elements.myEvents.innerHTML = state.myEvents.length
    ? state.myEvents
        .map(
          (event) => `
            <div class="list-item">
              <strong>${escapeHtml(event.title)}</strong><br />
              ${escapeHtml(getCategoryName(event.category_id))}<br />
              ${formatDate(event.event_date)}<br />
              Статус: ${escapeHtml(statusLabel(event.status))}
              <div class="list-item__actions">
                <button class="button button--ghost" data-participants-event="${event.id}">Участники</button>
                <button class="button button--ghost" data-edit-event="${event.id}">Редактировать</button>
                <button class="button button--ghost" data-status-event="${event.id}" data-status-value="published">Опубликовать</button>
                <button class="button button--ghost" data-status-event="${event.id}" data-status-value="archived">В архив</button>
                <button class="button button--ghost button--danger" data-delete-event="${event.id}">Удалить</button>
              </div>
            </div>
          `
        )
        .join("")
    : '<div class="empty-state">У вас пока нет созданных мероприятий.</div>';

  bindEventManagementActions(elements.myEvents);
}

function renderAdminUsers() {
  const searchValue = elements.adminUserSearch.value.trim().toLowerCase();
  const roleValue = elements.adminRoleFilter.value;
  const filteredUsers = state.users.filter((user) => {
    const haystack = `${user.full_name} ${user.email}`.toLowerCase();
    const matchesSearch = !searchValue || haystack.includes(searchValue);
    const matchesRole = !roleValue || user.role === roleValue;
    return matchesSearch && matchesRole;
  });

  if (!filteredUsers.length) {
    elements.adminUsers.innerHTML = '<div class="empty-state">Пользователи не найдены.</div>';
    return;
  }

  elements.adminUsers.innerHTML = `
    <div class="admin-users-table-wrap">
      <table class="admin-users-table">
        <thead>
          <tr>
            <th>Пользователь</th>
            <th>Роль</th>
            <th>Факультет</th>
            <th>Группа</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          ${filteredUsers
    .map(
      (user) => `
            <tr>
              <td>
                <div class="admin-user-main">
                  <strong>${escapeHtml(user.full_name)}</strong>
                  <div class="admin-user-email">${escapeHtml(user.email)}</div>
                </div>
              </td>
              <td><span class="badge">${escapeHtml(roleLabel(user.role))}</span></td>
              <td>${escapeHtml(user.faculty || "Не указан")}</td>
              <td>${escapeHtml(user.study_group || "Не указана")}</td>
              <td>
                <div class="admin-user-actions">
                  <select data-role-select="${user.id}">
                    <option value="student" ${user.role === "student" ? "selected" : ""}>Студент</option>
                    <option value="organizer" ${user.role === "organizer" ? "selected" : ""}>Организатор</option>
                    <option value="admin" ${user.role === "admin" ? "selected" : ""}>Администратор</option>
                  </select>
                  <button class="button button--ghost button--tiny" data-role-save="${user.id}">Сохранить</button>
                  <button class="button button--ghost button--tiny" data-user-delete="${user.id}">Удалить</button>
                </div>
              </td>
            </tr>
      `
    )
    .join("")}
        </tbody>
      </table>
    </div>
  `;

  document.querySelectorAll("[data-role-save]").forEach((button) => {
    button.addEventListener("click", () => {
      const userId = Number(button.dataset.roleSave);
      const select = document.querySelector(`[data-role-select="${userId}"]`);
      updateUserRole(userId, select.value);
    });
  });

  document.querySelectorAll("[data-user-delete]").forEach((button) => {
    button.addEventListener("click", () => {
      deleteUserItem(Number(button.dataset.userDelete));
    });
  });
}

function renderAdminEvents() {
  if (!state.manageableEvents.length) {
    elements.adminEvents.innerHTML = '<div class="empty-state">События не найдены.</div>';
    return;
  }

  elements.adminEvents.innerHTML = state.manageableEvents
    .map(
      (event) => `
        <div class="list-item">
          <strong>${escapeHtml(event.title)}</strong><br />
          ${escapeHtml(getCategoryName(event.category_id))}<br />
          ${formatDate(event.event_date)}<br />
          Статус: ${escapeHtml(statusLabel(event.status))}
          <div class="list-item__actions">
            <button class="button button--ghost" data-participants-event="${event.id}">Участники</button>
            <button class="button button--ghost" data-edit-event="${event.id}">Редактировать</button>
            <button class="button button--ghost" data-status-event="${event.id}" data-status-value="published">Опубликовать</button>
            <button class="button button--ghost" data-status-event="${event.id}" data-status-value="archived">В архив</button>
            <button class="button button--ghost button--danger" data-delete-event="${event.id}">Удалить</button>
          </div>
        </div>
      `
    )
    .join("");

  bindEventManagementActions(elements.adminEvents);
}

function bindEventManagementActions(scope) {
  scope.querySelectorAll("[data-participants-event]").forEach((button) => {
    button.addEventListener("click", () => {
      const eventId = Number(button.dataset.participantsEvent);
      loadParticipants(eventId, getEventTitle(eventId));
    });
  });
  scope.querySelectorAll("[data-edit-event]").forEach((button) => {
    button.addEventListener("click", () => startEventEditing(Number(button.dataset.editEvent)));
  });
  scope.querySelectorAll("[data-status-event]").forEach((button) => {
    button.addEventListener("click", () => {
      updateEventStatus(Number(button.dataset.statusEvent), button.dataset.statusValue);
    });
  });
  scope.querySelectorAll("[data-delete-event]").forEach((button) => {
    button.addEventListener("click", () => deleteEventItem(Number(button.dataset.deleteEvent)));
  });
}

function renderParticipants(title) {
  elements.participantsTitle.textContent = title;
  elements.participantsPanel.classList.remove("hidden");
  elements.participantsList.innerHTML = state.participants.length
    ? state.participants
        .map(
          (participant) => `
            <div class="list-item">
              <strong>${escapeHtml(participant.full_name)}</strong><br />
              Телефон: ${escapeHtml(participant.phone || "не указан")}<br />
              Email: ${escapeHtml(participant.email)}
            </div>
          `
        )
        .join("")
    : '<div class="empty-state">На это событие пока никто не записался.</div>';
}

async function loadCategories() {
  state.categories = await apiFetch("/categories");
  populateCategories();
}

async function loadEvents() {
  state.events = await apiFetch("/events");
  renderEvents();
}

async function loadCurrentUser() {
  if (!state.token) {
    state.currentUser = null;
    applyHeaderState();
    return;
  }

  try {
    state.currentUser = await apiFetch("/auth/me");
  } catch {
    state.token = "";
    state.currentUser = null;
    localStorage.removeItem("activity_token");
  }

  applyHeaderState();
  renderEvents();
}

async function loadProfileData() {
  if (!state.currentUser) {
    state.registrations = [];
    state.myEvents = [];
    renderProfile();
    return;
  }

  const [registrations, myEvents] = await Promise.all([
    apiFetch("/users/me/registrations"),
    apiFetch("/users/me/events"),
  ]);

  state.registrations = registrations;
  state.myEvents = myEvents;
  renderProfile();
}

async function loadManageableEvents() {
  if (!state.currentUser || !["organizer", "admin"].includes(state.currentUser.role)) {
    state.manageableEvents = [];
    renderAdminEvents();
    return;
  }

  state.manageableEvents = await apiFetch("/events/manage");
  state.myEvents = state.manageableEvents.filter((event) => event.organizer_id === state.currentUser.id);
  renderProfile();
  renderAdminEvents();
}

async function loadUsers() {
  if (!state.currentUser || state.currentUser.role !== "admin") {
    state.users = [];
    renderAdminUsers();
    return;
  }

  state.users = await apiFetch("/users");
  renderAdminUsers();
}

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());

  try {
    const response = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.token = response.access_token;
    localStorage.setItem("activity_token", state.token);
    await loadCurrentUser();
    await loadProfileData();
    await loadUsers();
    await loadManageableEvents();
    await loadEvents();
    setView("home");
    showToast("Вход выполнен");
    form.reset();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());

  Object.keys(payload).forEach((key) => {
    if (!payload[key]) {
      payload[key] = null;
    }
  });

  try {
    await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showToast("Аккаунт создан. Теперь можно войти.");
    form.reset();
    setView("login");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleCategoryCreate(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());

  try {
    await apiFetch("/categories", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await loadCategories();
    showToast("Категория добавлена");
    form.reset();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleEventCreate(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const isUnlimited = formData.get("is_unlimited") === "on";
  formData.set("category_id", String(Number(formData.get("category_id"))));
  formData.set("is_unlimited", String(isUnlimited));
  formData.set("event_date", new Date(formData.get("event_date")).toISOString());
  if (isUnlimited) {
    formData.delete("max_participants");
  }

  try {
    if (state.editingEventId) {
      await apiFetch(`/events/${state.editingEventId}`, { method: "PUT", body: formData });
      showToast("Событие обновлено");
    } else {
      await apiFetch("/events", { method: "POST", body: formData });
      showToast("Событие сохранено");
    }
    await loadEvents();
    await loadProfileData();
    await loadManageableEvents();
    form.reset();
    elements.limitField.classList.remove("hidden");
    resetEventForm();
    setView("profile");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function registerForEvent(eventId) {
  if (!state.currentUser) {
    showToast("Чтобы записаться, сначала войдите в аккаунт.", true);
    setView("login");
    return;
  }

  try {
    await apiFetch(`/events/${eventId}/register`, { method: "POST" });
    await loadProfileData();
    await loadManageableEvents();
    await loadEvents();
    showToast("Вы записались на мероприятие");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function cancelRegistration(eventId) {
  if (!state.currentUser) {
    return;
  }

  try {
    await apiFetch(`/events/${eventId}/register`, { method: "DELETE" });
    await loadProfileData();
    await loadManageableEvents();
    await loadEvents();
    showToast("Запись отменена");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function updateUserRole(userId, role) {
  try {
    await apiFetch(`/users/${userId}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
    await loadUsers();
    showToast("Роль пользователя обновлена");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function deleteUserItem(userId) {
  const user = state.users.find((item) => item.id === userId);
  const label = user ? `${user.full_name} (${user.email})` : `пользователя #${userId}`;
  const confirmed = window.confirm(
    `Удалить ${label}? Вместе с пользователем будут удалены его события и регистрации.`
  );

  if (!confirmed) {
    return;
  }

  try {
    await apiFetch(`/users/${userId}`, { method: "DELETE" });
    await Promise.all([loadUsers(), loadManageableEvents(), loadEvents(), loadProfileData()]);
    showToast("Пользователь удален");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function updateEventStatus(eventId, status) {
  try {
    await apiFetch(`/events/${eventId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    await loadEvents();
    await loadManageableEvents();
    showToast("Статус события обновлен");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function deleteEventItem(eventId) {
  const event = [...state.manageableEvents, ...state.myEvents, ...state.events].find((item) => item.id === eventId);
  const label = event ? `«${event.title}»` : `событие #${eventId}`;
  const confirmed = window.confirm(
    `Удалить ${label}? Вместе с событием будут удалены записи участников.`
  );

  if (!confirmed) {
    return;
  }

  try {
    await apiFetch(`/events/${eventId}`, { method: "DELETE" });
    await Promise.all([loadEvents(), loadManageableEvents(), loadProfileData()]);
    showToast("Событие удалено");
  } catch (error) {
    showToast(error.message, true);
  }
}

function bindRefreshButton(buttonId, loadingText, action) {
  document.getElementById(buttonId).addEventListener("click", (event) => {
    runWithButtonState(event.currentTarget, loadingText, action).catch((error) => {
      showToast(error.message, true);
    });
  });
}

async function loadParticipants(eventId, eventTitle) {
  try {
    state.participants = await apiFetch(`/events/${eventId}/participants`);
    renderParticipants(`Участники события: ${eventTitle}`);
    setView("profile");
  } catch (error) {
    showToast(error.message, true);
  }
}

function startEventEditing(eventId) {
  const event = state.manageableEvents.find((item) => item.id === eventId);
  if (!event) {
    showToast("Событие для редактирования не найдено", true);
    return;
  }

  state.editingEventId = eventId;
  elements.eventFormTitle.textContent = "Редактирование события";
  elements.cancelEditButton.classList.remove("hidden");

  elements.eventForm.elements.title.value = event.title;
  elements.eventForm.elements.short_description.value = event.short_description;
  elements.eventForm.elements.full_description.value = event.full_description;
  elements.eventForm.elements.event_date.value = new Date(event.event_date).toISOString().slice(0, 16);
  elements.eventForm.elements.location.value = event.location;
  elements.eventForm.elements.contacts.value = event.contacts;
  elements.eventForm.elements.format.value = event.format;
  elements.eventForm.elements.category_id.value = String(event.category_id);
  elements.eventForm.elements.status.value = event.status;
  elements.eventForm.elements.is_unlimited.checked = event.is_unlimited;
  if (event.is_unlimited) {
    elements.limitField.classList.add("hidden");
  } else {
    elements.limitField.classList.remove("hidden");
    elements.eventForm.elements.max_participants.value = event.max_participants ?? "";
  }

  setView("create");
}

function resetEventForm() {
  state.editingEventId = null;
  elements.eventFormTitle.textContent = "Создание события";
  elements.cancelEditButton.classList.add("hidden");
}

function handleLogout() {
  state.token = "";
  state.currentUser = null;
  state.registrations = [];
  state.myEvents = [];
  state.manageableEvents = [];
  state.users = [];
  state.participants = [];
  resetEventForm();
  localStorage.removeItem("activity_token");
  applyHeaderState();
  renderProfile();
  renderAdminUsers();
  renderAdminEvents();
  elements.participantsPanel.classList.add("hidden");
  renderEvents();
  setView("home");
  showToast("Вы вышли из аккаунта");
}

async function bootstrap() {
  try {
    await loadCategories();
    await loadEvents();
    await loadCurrentUser();
    await loadProfileData();
    await loadUsers();
    await loadManageableEvents();
    setView("home");
  } catch (error) {
    showToast(error.message, true);
  }
}

document.getElementById("login-form").addEventListener("submit", handleLogin);
document.getElementById("register-form").addEventListener("submit", handleRegister);
document.getElementById("event-form").addEventListener("submit", handleEventCreate);
document.getElementById("category-form").addEventListener("submit", handleCategoryCreate);
bindRefreshButton("refresh-events", "Обновление...", async () => {
  await loadEvents();
  showToast("События обновлены");
});
bindRefreshButton("refresh-profile-data", "Обновление...", async () => {
  await loadProfileData();
  showToast("Данные профиля обновлены");
});
bindRefreshButton("refresh-users", "Обновление...", async () => {
  await loadUsers();
  showToast("Список пользователей обновлен");
});
bindRefreshButton("refresh-manage-events", "Обновление...", async () => {
  await loadManageableEvents();
  showToast("Список событий обновлен");
});
elements.logoutButton.addEventListener("click", handleLogout);
elements.participantsClose.addEventListener("click", () => {
  elements.participantsPanel.classList.add("hidden");
});
elements.searchInput.addEventListener("input", renderEvents);
elements.categoryFilter.addEventListener("change", renderEvents);
elements.adminUserSearch.addEventListener("input", renderAdminUsers);
elements.adminRoleFilter.addEventListener("change", renderAdminUsers);
document.getElementById("unlimited-checkbox").addEventListener("change", (event) => {
  elements.limitField.classList.toggle("hidden", event.target.checked);
});
elements.cancelEditButton.addEventListener("click", () => {
  elements.eventForm.reset();
  elements.limitField.classList.remove("hidden");
  resetEventForm();
});

elements.navLinks.forEach((link) => {
  link.addEventListener("click", () => setView(link.dataset.view));
});
elements.userPill.addEventListener("click", () => setView("profile"));

bootstrap();
