function Home() {
  return (
    <div className="hero min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="hero-content flex-col lg:flex-row-reverse">
        <div className="text-center lg:text-left">
          <h1 className="text-5xl font-bold text-gray-900 dark:text-gray-100">Login now!</h1>
          <p className="py-6 text-gray-700 dark:text-gray-300">
            Provident cupiditate voluptatem et in. Quaerat fugiat ut assumenda excepturi exercitationem
            quasi. In deleniti eaque aut repudiandae et a id nisi.
          </p>
        </div>
        <div className="card w-full max-w-sm shrink-0 shadow-2xl bg-white dark:bg-gray-800">
          <div className="card-body p-6">
            <fieldset>
              <label className="label text-gray-700 dark:text-gray-200">Email</label>
              <input type="email" className="input input-bordered w-full mb-4 dark:bg-gray-700 dark:text-gray-100" placeholder="Email" />

              <label className="label text-gray-700 dark:text-gray-200">Password</label>
              <input type="password" className="input input-bordered w-full mb-2 dark:bg-gray-700 dark:text-gray-100" placeholder="Password" />

              <div className="mb-4">
                <a className="link link-hover text-blue-600 dark:text-blue-400">Forgot password?</a>
              </div>

              <button className="btn btn-neutral w-full dark:bg-blue-600 dark:hover:bg-blue-700">Login</button>
            </fieldset>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
